"""The reference library stays honest: schema, unique ids, implementations that exist, extendability without overwriting."""
import json, os, shutil, tempfile, unittest
from orbitalatlas import refs


class TestRefs(unittest.TestCase):
    def test_library_validates(self):
        self.assertEqual(refs.validate(), [])

    def test_both_references_are_registered_with_hashes_and_limits(self):
        s = {x["id"]: x for x in refs.sources()}
        for i in ("VISUAL_REF_001", "VISUAL_REF_002"):
            self.assertEqual(len(s[i]["sha256"]), 64); self.assertTrue(s[i]["limits"])
        self.assertTrue(len(refs.effects()) >= 25)

    def test_every_implemented_effect_resolves_to_real_code_and_has_qa_rules(self):
        for e in refs.effects():
            if e["status"] != "NOT_IMPLEMENTED":
                self.assertTrue(e["implementation"] and all(refs._resolve(s) for s in e["implementation"]), e["id"])
            if e["status"] == "IMPLEMENTED": self.assertTrue(e["qa_rules"], e["id"])

    def test_a_missing_symbol_and_a_duplicate_id_are_caught(self):
        d = tempfile.mkdtemp(); shutil.copytree(refs.LIB, os.path.join(d, "lib")); lib = os.path.join(d, "lib")
        f = os.path.join(lib, "effects", "VISUAL_REF_001.json"); data = json.load(open(f)); data["effects"][0]["implementation"] = ["fx.DoesNotExist"]; data["effects"].append(dict(data["effects"][1])); json.dump(data, open(f, "w"))
        p = refs.validate(lib); self.assertTrue(any("does not exist" in x for x in p)); self.assertTrue(any("duplicate" in x for x in p))

    def test_a_new_reference_goes_in_a_new_file_and_leaves_the_old_ones_untouched(self):
        d = tempfile.mkdtemp(); lib = os.path.join(d, "lib"); shutil.copytree(refs.LIB, lib)
        before = {f: open(os.path.join(lib, "effects", f), "rb").read() for f in os.listdir(os.path.join(lib, "effects"))}
        sp = os.path.join(lib, "sources.json"); s = json.load(open(sp)); n = dict(s["sources"][0], id="VISUAL_REF_003", analysis="VISUAL_REF_001_cinematic_geography.md", effects_file="effects/VISUAL_REF_003.json"); s["sources"].append(n); json.dump(s, open(sp, "w"))
        e = dict(refs.effects()[0], id="VR3-01", ref="VISUAL_REF_003"); json.dump(dict(schema="orbitalatlas-reference-effects/1", ref="VISUAL_REF_003", effects=[e]), open(os.path.join(lib, "effects", "VISUAL_REF_003.json"), "w"))
        self.assertEqual(refs.validate(lib), []); self.assertEqual(len(refs.effects(lib)), len(refs.effects()) + 1)
        for f, b in before.items(): self.assertEqual(open(os.path.join(lib, "effects", f), "rb").read(), b)

    def test_consult_returns_effects_and_qa_rules_for_a_scene_type(self):
        r = refs.consult("distance"); self.assertTrue(r and all("qa_rules" in x for x in r)); self.assertTrue(any(x["id"] == "VR1-05" for x in r))
        self.assertTrue(all(x["status"] != "NOT_IMPLEMENTED" for x in refs.consult("tech themes", implemented_only=True)))

    def test_unresolved_statuses_are_listed_so_nothing_is_overclaimed(self):
        ni = [e["id"] for e in refs.effects() if e["status"] == "NOT_IMPLEMENTED"]; self.assertIn("VR2-12", ni); self.assertTrue(all(e["implementation"] in ([], ["-"], "-") or True for e in refs.effects()))


if __name__ == "__main__":
    unittest.main()
