import json
import unittest
from pathlib import Path

from mcp_setup import add_command, expand, pick, review, rule_matches, tool_name

HERE = Path(__file__).resolve().parent
SAMPLE = json.loads((HERE / "sample_mcp.json").read_text(encoding="utf-8"))


class AddCommand(unittest.TestCase):
    def test_a_remote_server(self):
        self.assertEqual(add_command("notion", url="https://mcp.notion.com/mcp"),
                         ["claude", "mcp", "add", "--transport", "http", "--scope", "local", "notion",
                          "https://mcp.notion.com/mcp"])

    def test_a_local_server_puts_its_command_after_the_double_dash(self):
        words = add_command("files", command="npx", args=["-y", "server", "--port", "8080"], scope="project")
        self.assertEqual(words[:4], ["claude", "mcp", "add", "--transport"])
        self.assertIn("stdio", words)
        self.assertEqual(words[words.index("--scope") + 1], "project")
        cut = words.index("--")
        self.assertEqual(words[cut + 1:], ["npx", "-y", "server", "--port", "8080"])
        self.assertIn("files", words[:cut])

    def test_env_pairs_and_the_name_never_right_after_env(self):
        words = add_command("airtable", command="npx", args=["-y", "airtable-mcp-server"],
                            env={"AIRTABLE_API_KEY": "k1", "MODE": "read"})
        cut = words.index("--")
        options = words[:cut]
        self.assertIn("AIRTABLE_API_KEY=k1", options)
        self.assertIn("MODE=read", options)
        for i, word in enumerate(options):
            if word == "--env":
                self.assertIn("=", options[i + 1])
                self.assertNotEqual(options[i + 1], "airtable")
        self.assertNotEqual(options[options.index("airtable") - 1], "--env")

    def test_bad_calls(self):
        with self.assertRaises(ValueError):
            add_command("x", url="https://a.example/mcp", scope="team")
        with self.assertRaises(ValueError):
            add_command("x")
        with self.assertRaises(ValueError):
            add_command("x", url="https://a.example/mcp", command="npx")
        with self.assertRaises(ValueError):
            add_command("x", url="https://a.example/mcp", env={"KEY": "v"})


class Expand(unittest.TestCase):
    def test_a_set_variable(self):
        self.assertEqual(expand("Bearer ${API_KEY}", {"API_KEY": "abc"}), ("Bearer abc", []))

    def test_a_default(self):
        self.assertEqual(expand("${BASE:-https://api.example.com}/mcp", {}), ("https://api.example.com/mcp", []))
        self.assertEqual(expand("${BASE:-https://api.example.com}/mcp", {"BASE": "https://b.example"}),
                         ("https://b.example/mcp", []))

    def test_a_missing_variable_stays_as_written(self):
        self.assertEqual(expand("Bearer ${TOKEN}", {}), ("Bearer ${TOKEN}", ["TOKEN"]))

    def test_several_variables(self):
        text, missing = expand("${A}-${B:-b}-${C}", {"A": "a"})
        self.assertEqual(text, "a-b-${C}")
        self.assertEqual(missing, ["C"])

    def test_plain_text(self):
        self.assertEqual(expand("npx -y server", {"X": "1"}), ("npx -y server", []))


class Pick(unittest.TestCase):
    def test_local_wins_then_project_then_user(self):
        local = {"db": {"command": "local-db"}}
        project = {"db": {"command": "project-db"}, "docs": {"type": "http", "url": "https://p.example"}}
        user = {"docs": {"type": "http", "url": "https://u.example"}, "notes": {"command": "notes"}}
        chosen = pick(local, project, user)
        self.assertEqual(chosen["db"], ("local", {"command": "local-db"}))
        self.assertEqual(chosen["docs"], ("project", {"type": "http", "url": "https://p.example"}))
        self.assertEqual(chosen["notes"], ("user", {"command": "notes"}))
        self.assertEqual(sorted(chosen), ["db", "docs", "notes"])

    def test_entries_are_never_merged(self):
        chosen = pick({"a": {"command": "x"}}, {}, {"a": {"command": "y", "env": {"K": "v"}}})
        self.assertEqual(chosen["a"], ("local", {"command": "x"}))


class Review(unittest.TestCase):
    def test_the_sample(self):
        self.assertEqual(review(SAMPLE), [("crm", "secret"), ("helper", "command"), ("wiki", "no-type")])

    def test_a_clean_file(self):
        clean = {"mcpServers": {
            "files": {"command": "npx", "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp/x"]},
            "api": {"type": "http", "url": "${API_BASE_URL:-https://api.example.com}/mcp",
                    "headers": {"Authorization": "Bearer ${API_KEY}"}},
            "local": {"command": "python3", "args": ["server.py"], "env": {"API_TOKEN": "${MY_TOKEN}", "MODE": "ro"}}}}
        self.assertEqual(review(clean), [])

    def test_not_https(self):
        config = {"mcpServers": {"plain": {"type": "http", "url": "http://tools.example.com/mcp"}}}
        self.assertEqual(review(config), [("plain", "not-https")])

    def test_a_secret_in_env(self):
        config = {"mcpServers": {"db": {"command": "python3", "args": ["db.py"],
                                        "env": {"DB_PASSWORD": "hunter2", "MODE": "ro"}}}}
        self.assertEqual(review(config), [("db", "secret")])

    def test_risky_commands(self):
        for line in (["sudo", "server"], ["bash", "-c", "a; b"], ["sh", "-c", "wget x"], ["rm", "-rf", "/x"]):
            config = {"mcpServers": {"s": {"command": line[0], "args": line[1:]}}}
            self.assertEqual(review(config), [("s", "command")], line)

    def test_several_kinds_on_one_server(self):
        config = {"mcpServers": {"bad": {"url": "http://x.example/mcp", "headers": {"X-API-Key": "abc"}}}}
        self.assertEqual(review(config), [("bad", "no-type"), ("bad", "not-https"), ("bad", "secret")])

    def test_an_empty_file(self):
        self.assertEqual(review({}), [])


class Rules(unittest.TestCase):
    def test_tool_name(self):
        self.assertEqual(tool_name("files", "read_file"), "mcp__files__read_file")

    def test_a_whole_server(self):
        self.assertTrue(rule_matches("mcp__files", "files", "read_file"))
        self.assertTrue(rule_matches("mcp__files__*", "files", "write_file"))

    def test_one_tool(self):
        self.assertTrue(rule_matches("mcp__files__read_file", "files", "read_file"))
        self.assertFalse(rule_matches("mcp__files__read_file", "files", "write_file"))

    def test_wildcards(self):
        self.assertTrue(rule_matches("mcp__*", "files", "read_file"))
        self.assertTrue(rule_matches("mcp__*", "tickets", "search"))
        self.assertTrue(rule_matches("mcp__files__read_*", "files", "read_file"))
        self.assertFalse(rule_matches("mcp__files__read_*", "files", "write_file"))
        self.assertFalse(rule_matches("mcp__tickets__*", "files", "read_file"))

    def test_other_servers_and_rules(self):
        self.assertFalse(rule_matches("mcp__files", "filesystem", "read_file"))
        self.assertFalse(rule_matches("mcp__fil", "files", "read_file"))
        self.assertFalse(rule_matches("Bash", "files", "read_file"))
        self.assertFalse(rule_matches("mcp__tickets__*", "files", "read_file"))


if __name__ == "__main__":
    unittest.main()
