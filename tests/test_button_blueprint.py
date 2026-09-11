"""Exercise the shipped blueprint templates without a running Home Assistant."""
from __future__ import annotations

import ast
import json
from pathlib import Path
from types import SimpleNamespace
import unittest

from jinja2 import StrictUndefined
from jinja2.sandbox import SandboxedEnvironment
import yaml

ROOT = Path(__file__).resolve().parents[1]
BLUEPRINTS = ROOT / "blueprints/automation/vuplus_hid_raw"


class BlueprintLoader(yaml.SafeLoader):
    """Preserve Home Assistant input references during YAML loading."""


BlueprintLoader.add_constructor(
    "!input", lambda loader, node: {"__input__": loader.construct_scalar(node)}
)


def load(language="de"):
    suffix = ".en" if language == "en" else ""
    return yaml.load(
        (BLUEPRINTS / f"short_press_buttons{suffix}.yaml").read_text(encoding="utf-8"),
        Loader=BlueprintLoader,
    )


def target_choice(entity_id):
    """Build the same selection object as the type selector."""
    choices = load()["blueprint"]["input"]["alternative_button_targets"]["selector"]["object"]["fields"]["typed_target"]["selector"]["choose"]["choices"]
    label = next((name for name, config in choices.items()
                  if config["selector"]["entity"]["filter"][0]["domain"] == entity_id.split('.')[0]), "Unsupported")
    return {"active_choice": label, label: entity_id}


def target_row(command, entity_id):
    if not entity_id:
        return {"command": command, "disabled": True}
    return {"command": command, "typed_target": target_choice(entity_id)}


class BlueprintTest(unittest.TestCase):
    def run_blueprint(self, command="ok", event_type="press_end", entities=None,
                      device_members=None, keycodes=None, havu_entities=None,
                      available_services=None, include_data=False, **inputs):
        """Run the actual YAML's supported actions with simulated HA state helpers.

        This is a template/behaviour test, not HA's schema or execution engine.
        """
        blueprint = load()
        config = {k: v.get("default") for k, v in blueprint["blueprint"]["input"].items()}
        config.update(inputs)

        def expand(value):
            if isinstance(value, dict):
                if set(value) == {"__input__"}:
                    return config[value["__input__"]]
                return {k: expand(v) for k, v in value.items()}
            if isinstance(value, list):
                return [expand(v) for v in value]
            return value

        data = expand(blueprint)
        if event_type not in data["triggers"][0]["options"]["event_type"]:
            return []
        entities = entities if entities is not None else {"button.receiver_ok": "unknown"}
        env = SandboxedEnvironment(undefined=StrictUndefined)
        context = {
            "trigger": SimpleNamespace(to_state=SimpleNamespace(attributes={"command": command})),
            "states": SimpleNamespace(button=[
                SimpleNamespace(entity_id=key, attributes={"keycode": (keycodes or {}).get(key)})
                for key in entities if key.startswith("button.")
            ]),
            "is_state": lambda entity, state: entities.get(entity) == state,
            "device_entities": lambda device: (device_members or {}).get(device, []),
            "integration_entities": lambda domain: list(entities) if havu_entities is None else havu_entities,
            "expand": lambda entity: [SimpleNamespace(entity_id=entity)] if entity in entities else [],
            "has_service": lambda domain, service: available_services is None or f"{domain}.{service}" in available_services,
        }

        def render(value):
            if not isinstance(value, str) or "{{" not in value and "{%" not in value:
                return value
            rendered = env.from_string(value).render(context).strip()
            try:
                return ast.literal_eval(rendered)
            except (ValueError, SyntaxError):
                return rendered

        def variables(values):
            for key, value in values.items():
                context[key] = render(value)

        def condition(value):
            if value["condition"] == "and":
                return all(condition(c) for c in value["conditions"])
            if value["condition"] == "state":
                return entities.get(value["entity_id"]) == value["state"]
            return bool(render(value["value_template"]))

        calls = []

        def execute(actions):
            for action in actions:
                if "variables" in action:
                    variables(action["variables"])
                elif "choose" in action:
                    for branch in action["choose"]:
                        if all(condition(c) for c in branch["conditions"]):
                            execute(branch["sequence"])
                            break
                elif "condition" in action:
                    if not condition(action):
                        return
                else:
                    call = (render(action["action"]), render(action["target"]["entity_id"]))
                    calls.append((*call, render(action.get("data", {}))) if include_data else call)

        variables(data["variables"])
        execute(data["actions"])
        return calls

    def test_same_logic_inputs_and_defaults_in_both_languages(self):
        def without_labels(value):
            if isinstance(value, dict):
                if "choices" in value:
                    return {"choices": {
                        choice["selector"]["entity"]["filter"][0]["domain"]: without_labels(choice)
                        for choice in value["choices"].values()
                    }}
                return {key: without_labels(child) for key, child in value.items() if key != "label"}
            if isinstance(value, list):
                return [without_labels(child) for child in value]
            return value

        de, en = load(), load("en")
        for data in (de, en):
            meta = data.pop("blueprint")
            self.assertEqual(meta["homeassistant"]["min_version"], "2026.9.0")
            for field in meta["input"].values():
                field.pop("name")
                field.pop("description", None)
            data["inputs"] = meta["input"]
        self.assertEqual(without_labels(de), without_labels(en))

    def test_alternative_target_selectors_cover_translated_keys_and_buttons(self):
        for language in ("de", "en"):
            inputs = load(language)["blueprint"]["input"]
            selection = inputs["alternative_button_targets"]
            self.assertEqual(selection["default"], [])
            obj = selection["selector"]["object"]
            self.assertTrue(obj["multiple"])
            fields = obj["fields"]
            self.assertTrue(fields["command"]["required"])
            labels = json.loads((ROOT / f"custom_components/vuplus_hid_raw/translations/{language}.json").read_text(encoding="utf-8"))["entity"]["event"]
            options = fields["command"]["selector"]["select"]["options"]
            self.assertEqual({item["value"]: item["label"] for item in options},
                             {key: value["name"] for key, value in labels.items()})
            domains = load()["variables"]["default_actions"]
            self.assertNotIn("entity_id", fields)
            self.assertNotIn("alternative_buttons", inputs)
            choices = fields["typed_target"]["selector"]["choose"]["choices"]
            self.assertEqual(len(choices), len(domains))
            self.assertEqual({choice["selector"]["entity"]["filter"][0]["domain"]
                              for choice in choices.values()}, set(domains))
            actions = {option["value"] for option in fields["action"]["selector"]["select"]["options"]}
            self.assertEqual({action.split(".")[0] for action in actions}, set(domains))
            self.assertTrue(set(domains.values()) <= actions)
            for choice in choices.values():
                self.assertEqual(set(choice["selector"]), {"entity"})
            self.assertNotIn("required", fields["typed_target"])
            self.assertEqual(fields["disabled"]["selector"], {"boolean": {}})

    def test_selected_alternative_overrides_default_only_when_active(self):
        for enabled, target in ((False, "button.default"), (True, "button.selected")):
            self.assertEqual(self.run_blueprint(alternative_enabled=enabled,
                default_buttons={"ok": "button.default"},
                alternative_button_targets=[{"command": "ok", "typed_target": target_choice("button.selected")}],
                entities=dict.fromkeys(["button.default", "button.selected"], "unknown")),
                [("button.press", target)])

    def test_typed_target_uses_only_active_type_in_both_languages(self):
        for language in ("de", "en"):
            choices = load(language)["blueprint"]["input"]["alternative_button_targets"]["selector"]["object"]["fields"]["typed_target"]["selector"]["choose"]["choices"]
            for label, choice in choices.items():
                domain = choice["selector"]["entity"]["filter"][0]["domain"]
                target = f"{domain}.selected"
                with self.subTest(language=language, domain=domain):
                    self.assertEqual(self.run_blueprint(alternative_enabled=True,
                        alternative_button_targets=[{"command": "ok",
                            "typed_target": {"active_choice": label, label: target, "inactive": "button.other"}}],
                        entities={target: "unknown", "button.old": "unknown", "button.other": "unknown"}),
                        [(load()["variables"]["default_actions"][domain], target)])

    def test_every_offered_action_with_matching_entity(self):
        for language in ("de", "en"):
            fields = load(language)["blueprint"]["input"]["alternative_button_targets"]["selector"]["object"]["fields"]
            choices = fields["typed_target"]["selector"]["choose"]["choices"]
            for option in fields["action"]["selector"]["select"]["options"]:
                action = option["value"]
                domain = action.split(".")[0]
                label = next(label for label, choice in choices.items()
                             if choice["selector"]["entity"]["filter"][0]["domain"] == domain)
                target = f"{domain}.selected"
                with self.subTest(language=language, action=action):
                    self.assertEqual(self.run_blueprint(alternative_enabled=True,
                        alternative_button_targets=[{"command": "ok", "action": action,
                            "typed_target": {"active_choice": label, label: target, "inactive": "button.other"}}],
                        entities={target: "unknown", "button.other": "unknown"}), [(action, target)])

    def test_incomplete_typed_target_does_not_select_an_inactive_type(self):
        for choice in ({}, {"active_choice": "Media Player"},
                       {"active_choice": "Media Player", "Schalter": "switch.inactive"}):
            self.assertEqual(self.run_blueprint(alternative_enabled=True,
                alternative_button_targets=[{"command": "ok", "typed_target": choice}]), [])

    def test_typed_target_keeps_action_data_and_disable_priority(self):
        row = {"command": "mute", "typed_target": target_choice("media_player.amp"), "action": "media_player.volume_mute", "data": {"is_volume_muted": True}}
        self.assertEqual(self.run_blueprint("mute", alternative_enabled=True, include_data=True,
            alternative_button_targets=[row], entities={"media_player.amp": "playing"}),
            [("media_player.volume_mute", "media_player.amp", {"is_volume_muted": True})])
        self.assertEqual(self.run_blueprint("mute", alternative_enabled=True,
            alternative_button_targets=[{**row, "disabled": True}], entities={"media_player.amp": "playing"}), [])

    def test_selected_alternative_disable_wins_over_target_and_default(self):
        for row in ({"command": "ok", "disabled": True},
                    {"command": "ok", "disabled": True, "typed_target": target_choice("button.receiver_ok")}):
            self.assertEqual(self.run_blueprint(alternative_enabled=True,
                default_prefix="button.receiver_", alternative_button_targets=[row]), [])

    def test_selected_alternative_incomplete_rows_keep_existing_mapping(self):
        for row in ({"command": "ok"}, {"command": "ok", "disabled": False}):
            self.assertEqual(self.run_blueprint(alternative_enabled=True,
                default_buttons={"ok": "button.receiver_ok"}, alternative_button_targets=[row]),
                [("button.press", "button.receiver_ok")])

    def test_selected_alternative_last_complete_row_and_numeric_key(self):
        self.assertEqual(self.run_blueprint("1", alternative_enabled=True,
            alternative_button_targets=[{"command": "1", "disabled": True},
                {"command": "1", "typed_target": target_choice("button.receiver_ok")}, {"command": "1"}]),
            [("button.press", "button.receiver_ok")])

    def test_selected_alternative_applies_to_entire_receiver_profile(self):
        self.assertEqual(self.run_blueprint(alternative_enabled=True, alternative_receiver="receiver",
            alternative_button_targets=[{"command": "ok", "typed_target": target_choice("button.receiver_ok")}]),
            [("button.press", "button.receiver_ok")])

    def test_alternative_entities_use_domain_defaults(self):
        expected = {
            "input_button": "press", "script": "turn_on", "scene": "turn_on",
            "switch": "toggle", "input_boolean": "toggle", "light": "toggle",
            "fan": "toggle", "cover": "toggle", "media_player": "media_play_pause",
        }
        for domain, service in expected.items():
            target = f"{domain}.living_room"
            with self.subTest(domain=domain):
                self.assertEqual(self.run_blueprint(alternative_enabled=True,
                    alternative_button_targets=[{"command": "ok", "typed_target": target_choice(target)}],
                    entities={target: "off"}), [(f"{domain}.{service}", target)])

    def test_media_player_volume_action_and_script_parameters(self):
        for command, target, action, data in (
            ("volume_up", "media_player.amp", "media_player.volume_up", {}),
            ("volume_down", "media_player.amp", "media_player.volume_down", {}),
            ("mute", "media_player.amp", "media_player.volume_mute", {"is_volume_muted": True}),
            ("red", "script.cinema", "script.turn_on", {"variables": {"mode": "movie"}}),
            ("blue", "light.room", "light.turn_on", {"brightness_pct": 30}),
        ):
            with self.subTest(command=command):
                self.assertEqual(self.run_blueprint(command, alternative_enabled=True, include_data=True,
                    alternative_button_targets=[{"command": command, "typed_target": target_choice(target), "action": action, "data": data}],
                    entities={target: "off"}), [(action, target, data)])

    def test_mismatched_unavailable_missing_and_unsupported_actions_are_skipped(self):
        for row, entities, services in (
            ({"typed_target": target_choice("switch.amp"), "action": "button.press"}, {"switch.amp": "off"}, None),
            ({"typed_target": target_choice("sensor.temp")}, {"sensor.temp": "20"}, None),
            ({"typed_target": target_choice("switch.amp")}, {"switch.amp": "unavailable"}, None),
            ({"typed_target": target_choice("switch.missing")}, {}, None),
            ({"typed_target": target_choice("switch.amp")}, {"switch.amp": "off"}, []),
            ({"typed_target": target_choice("switch.amp"), "data": ["invalid"]}, {"switch.amp": "off"}, None),
        ):
            with self.subTest(row=row):
                self.assertEqual(self.run_blueprint(alternative_enabled=True,
                    default_prefix="button.receiver_",
                    alternative_button_targets=[{"command": "ok", **row}],
                    entities={"button.receiver_ok": "unknown", **entities}, available_services=services), [])

    def test_generic_targets_obey_conditions_and_disable(self):
        for conditions, disabled, expected in (
            ([], False, [("switch.toggle", "switch.amp")]),
            ([], True, []),
            ([{"condition": "template", "value_template": "{{ false }}"}], False,
             [("button.press", "button.receiver_ok")]),
        ):
            self.assertEqual(self.run_blueprint(alternative_enabled=True, alternative_conditions=conditions,
                default_prefix="button.receiver_", entities={"button.receiver_ok": "unknown", "switch.amp": "off"},
                alternative_button_targets=[{"command": "ok", "typed_target": target_choice("switch.amp"), "disabled": disabled}]), expected)

    def test_remote_device_scope_and_queued_order(self):
        data = load()
        self.assertEqual(data["triggers"][0]["trigger"], "event.received")
        self.assertEqual(data["triggers"][0]["target"], {"device_id": {"__input__": "remote"}})
        self.assertEqual(data["mode"], "queued")

    def test_only_short_release_dispatches(self):
        for event in ("press_start", "long_press_start", "long_press_end", "repeat"):
            self.assertEqual(self.run_blueprint(event_type=event, default_prefix="button.receiver_"), [])
        self.assertEqual(self.run_blueprint(default_prefix="button.receiver_"), [("button.press", "button.receiver_ok")])

    def test_alias_and_numeric_keys(self):
        for command, aliases, target in (
            ("volume_up", {"volume_up": "lautstarke_plus"}, "button.receiver_lautstarke_plus"),
            ("1", {}, "button.receiver_1"),
            ("0", {"0": "digit_0"}, "button.receiver_digit_0"),
        ):
            self.assertEqual(self.run_blueprint(command, default_prefix="button.receiver_", command_aliases=aliases,
                                               entities={target: "unknown"}), [("button.press", target)])

    def test_explicit_target_beats_alias_and_prefix(self):
        self.assertEqual(self.run_blueprint(default_prefix="button.other_", command_aliases={"ok": "enter"},
                                           default_buttons={"ok": "button.receiver_ok"}), [("button.press", "button.receiver_ok")])

    def test_disabled_missing_unavailable_and_wrong_domain_targets(self):
        for target in ("", None, "button.missing", "light.receiver_ok", "button.offline", ["button.receiver_ok"]):
            with self.subTest(target=target):
                self.assertEqual(self.run_blueprint(default_prefix="button.receiver_", default_buttons={"ok": target},
                    entities={"button.receiver_ok": "unknown", "button.offline": "unavailable", "light.receiver_ok": "on"}), [])

    def test_no_prefix_uses_only_explicit_targets(self):
        self.assertEqual(self.run_blueprint(), [])
        self.assertEqual(self.run_blueprint(default_buttons={"ok": "button.receiver_ok"}), [("button.press", "button.receiver_ok")])

    def test_alternative_requires_enable_and_matching_conditions(self):
        for enabled, matching in ((False, True), (True, False), (True, True)):
            target = "button.amplifier_ok" if enabled and matching else "button.receiver_ok"
            calls = self.run_blueprint(default_prefix="button.receiver_", alternative_enabled=enabled,
                alternative_conditions=[{"condition": "state", "entity_id": "input_boolean.cinema", "state": "on"}],
                alternative_button_targets=[target_row("ok", "button.amplifier_ok")], entities={
                    "button.amplifier_ok": "unknown", "button.receiver_ok": "unknown",
                    "input_boolean.cinema": "on" if matching else "off"})
            self.assertEqual(calls, [("button.press", target)])

    def test_alternative_condition_can_reference_current_command(self):
        self.assertEqual(self.run_blueprint(alternative_enabled=True,
            alternative_conditions=[{"condition": "template", "value_template": "{{ command == 'ok' }}"}],
            alternative_button_targets=[target_row("ok", "button.receiver_ok")]), [("button.press", "button.receiver_ok")])

    def test_partial_alternative_inherits_untouched_explicit_targets(self):
        self.assertEqual(self.run_blueprint(alternative_enabled=True, default_buttons={"ok": "button.receiver_ok"},
            alternative_button_targets=[target_row("volume_up", "button.amplifier_up")]), [("button.press", "button.receiver_ok")])

    def test_full_alternative_does_not_inherit_default_targets_or_fall_back(self):
        kwargs = dict(alternative_enabled=True, default_prefix="button.receiver_",
                      default_buttons={"ok": "button.receiver_ok"}, alternative_prefix="button.other_")
        self.assertEqual(self.run_blueprint(**kwargs), [])
        self.assertEqual(self.run_blueprint(**kwargs, entities={"button.other_ok": "unknown"}), [("button.press", "button.other_ok")])

    def test_alternative_can_disable_a_default_key(self):
        self.assertEqual(self.run_blueprint(alternative_enabled=True, default_prefix="button.receiver_",
                                           alternative_button_targets=[target_row("ok", "")]), [])

    def test_havu_mapping_matches_pinned_receiver_key_map(self):
        from test_event_entity_source import integration

        fixture = json.loads((ROOT / "tests/fixtures/havuopenwebif_key_map.json").read_text(encoding="utf-8"))
        self.assertIn(fixture["commit"], fixture["source"])
        self.assertEqual(fixture["verification_scope"], "source_review_and_simulated_blueprint_tests")
        for language, suffix in (("de", ""), ("en", ".en")):
            description = load(language)["blueprint"]["description"]
            self.assertIn(f"HAVUOpenWebif {fixture['version']}", description)
            self.assertIn(fixture["commit"], description)
            for name in ("README", "DOKUMENTATION"):
                document = (ROOT / f"{name}{suffix}.md").read_text(encoding="utf-8")
                self.assertIn(f"HAVUOpenWebif {fixture['version']}", document)
                self.assertIn(fixture["commit"][:12], document)
        mapping = load()["variables"]["havu_keycodes"]
        self.assertEqual(set(mapping), set(integration.COMMAND_LABELS) - {"speak", "left_0", "right_0"})
        renamed = {"stb_power": "power", "forward": "fast_forward", "teletext": "text"}
        for command, code in mapping.items():
            with self.subTest(command=command):
                self.assertEqual(code, fixture["key_map"][renamed.get(command, command)])
                target = "button.beliebig_umbenannt"
                self.assertEqual(self.run_blueprint(command, default_receiver="receiver",
                    entities={target: "unknown"}, keycodes={target: code},
                    device_members={"receiver": [target]}), [("button.press", target)])

    def test_havu_uses_receiver_scope_and_integration(self):
        targets = {"button.first": "unknown", "button.second": "unknown", "button.foreign": "unknown"}
        self.assertEqual(self.run_blueprint(default_receiver="second", entities=targets,
            keycodes=dict.fromkeys(targets, 352), havu_entities=["button.first", "button.second"],
            device_members={"first": ["button.first"], "second": ["button.second", "button.foreign"]}),
            [("button.press", "button.second")])

    def test_havu_ambiguous_codes_require_explicit_mapping(self):
        for command, code in (("tv", 377), ("teletext", 388)):
            kwargs = dict(default_receiver="receiver", entities={"button.a": "unknown", "button.b": "unknown"},
                          keycodes={"button.a": code, "button.b": code},
                          device_members={"receiver": ["button.a", "button.b"]})
            self.assertEqual(self.run_blueprint(command, **kwargs), [])
            self.assertEqual(self.run_blueprint(command, **kwargs, default_buttons={command: "button.b"}),
                             [("button.press", "button.b")])

    def test_havu_missing_unsupported_or_unavailable_never_falls_back_to_prefix(self):
        for command in ("ok", "speak", "left_0", "right_0"):
            self.assertEqual(self.run_blueprint(command, default_receiver="receiver",
                default_prefix="button.receiver_"), [])
        self.assertEqual(self.run_blueprint(default_receiver="receiver",
            entities={"button.offline": "unavailable"}, keycodes={"button.offline": 352},
            device_members={"receiver": ["button.offline"]}), [])

    def test_havu_alternative_receiver_and_partial_override(self):
        kwargs = dict(default_receiver="first", alternative_enabled=True,
                      entities={"button.first": "unknown", "button.second": "unknown"},
                      keycodes={"button.first": 352, "button.second": 352},
                      device_members={"first": ["button.first"], "second": ["button.second"]})
        self.assertEqual(self.run_blueprint(**kwargs, alternative_receiver="second",
            default_buttons={"ok": "button.first"}), [("button.press", "button.second")])
        self.assertEqual(self.run_blueprint(**kwargs, alternative_button_targets=[target_row("mute", "button.second")]),
                         [("button.press", "button.first")])
        self.assertEqual(self.run_blueprint(**kwargs, alternative_button_targets=[target_row("ok", "button.second")]),
                         [("button.press", "button.second")])
        self.assertEqual(self.run_blueprint(**kwargs, alternative_prefix="button.other_"), [])
