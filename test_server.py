import json
import unittest

import server


STEP_2_9_TEST_CASES = [
    {
        "id": "TC1",
        "type": "Positive",
        "description": "Extract two existing fields from a simple API response.",
        "input": {
            "raw_response": {
                "name": "Alice",
                "email": "alice@example.com",
                "age": 30,
            },
            "target_fields": ["name", "email"],
        },
        "expected_output": {
            "cleaned_response": {
                "name": "Alice",
                "email": "alice@example.com",
            },
            "missing_fields": [],
            "removed_fields": ["age"],
        },
    },
    {
        "id": "TC2",
        "type": "Positive",
        "description": "Preserve nested object values while filtering top-level fields.",
        "input": {
            "raw_response": {
                "user": {"id": 101, "role": "admin"},
                "status": "active",
                "region": "us-east",
            },
            "target_fields": ["user", "status"],
        },
        "expected_output": {
            "cleaned_response": {
                "user": {"id": 101, "role": "admin"},
                "status": "active",
            },
            "missing_fields": [],
            "removed_fields": ["region"],
        },
    },
    {
        "id": "TC3",
        "type": "Positive",
        "description": "Preserve target_fields ordering in cleaned_response.",
        "input": {
            "raw_response": {
                "id": 5001,
                "name": "Widget",
                "price": 19.99,
                "currency": "USD",
            },
            "target_fields": ["price", "name"],
        },
        "expected_output": {
            "cleaned_response": {
                "price": 19.99,
                "name": "Widget",
            },
            "missing_fields": [],
            "removed_fields": ["id", "currency"],
        },
    },
    {
        "id": "TC4",
        "type": "Positive",
        "description": "Allow empty target_fields and remove all input fields.",
        "input": {
            "raw_response": {
                "session_id": "S-123",
                "expires_at": "2026-05-13T12:00:00Z",
            },
            "target_fields": [],
        },
        "expected_output": {
            "cleaned_response": {},
            "missing_fields": [],
            "removed_fields": ["session_id", "expires_at"],
        },
    },
    {
        "id": "TC5",
        "type": "Positive",
        "description": "Report missing target fields without generating them.",
        "input": {
            "raw_response": {
                "order_id": "ORD-900",
                "total": 250,
                "status": "paid",
            },
            "target_fields": ["status", "customer_id"],
        },
        "expected_output": {
            "cleaned_response": {
                "status": "paid",
            },
            "missing_fields": ["customer_id"],
            "removed_fields": ["order_id", "total"],
        },
    },
    {
        "id": "TC6",
        "type": "Negative",
        "description": "No target fields exist in raw_response, so no cleaned fields are returned.",
        "input": {
            "raw_response": {
                "name": "Bob",
                "email": "bob@example.com",
            },
            "target_fields": ["phone", "address"],
        },
        "expected_output": {
            "cleaned_response": {},
            "missing_fields": ["phone", "address"],
            "removed_fields": ["name", "email"],
        },
    },
    {
        "id": "TC7",
        "type": "Negative",
        "description": "Reject unexpected extra argument fields outside the schema.",
        "input": {
            "raw_response": {"name": "Ada"},
            "target_fields": ["name"],
            "extra_field": "unexpected",
        },
        "expected_error": {
            "code": -32602,
            "message": "Only 'raw_response' and 'target_fields' are allowed.",
        },
    },
    {
        "id": "TC8",
        "type": "Negative",
        "description": "Reject invalid target_fields entries when a field name is empty.",
        "input": {
            "raw_response": {"name": "Ada"},
            "target_fields": ["name", ""],
        },
        "expected_error": {
            "code": -32602,
            "message": "The 'target_fields[1]' field must be a non-empty string.",
        },
    },
]


class APIResponseCleanerMCPTests(unittest.TestCase):
    def test_initialize_returns_protocol_server_and_capabilities(self):
        result = server.handle_mcp_request(
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
        )
        self.assertEqual(
            result,
            {
                "jsonrpc": "2.0",
                "id": 1,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "serverInfo": {
                        "name": "api-response-cleaner-mcp",
                        "version": "0.1.0",
                    },
                    "capabilities": {"tools": {}},
                },
            },
        )

    def test_tools_list_returns_single_tool_with_annotations_and_safety_metadata(self):
        result = server.handle_mcp_request(
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
        )
        tool = result["result"]["tools"][0]
        self.assertEqual(len(result["result"]["tools"]), 1)
        self.assertEqual(tool["name"], "apiResponseCleaner")
        self.assertIn("annotations", tool)
        self.assertIn("meta", tool)
        self.assertEqual(tool["meta"]["audit"]["deterministic"], True)

    def test_positive_case_1_filters_requested_fields_only(self):
        case = STEP_2_9_TEST_CASES[0]
        result = server.handle_mcp_request(
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "apiResponseCleaner",
                    "arguments": case["input"],
                },
            }
        )
        self.assertEqual(
            result["result"]["structuredContent"],
            case["expected_output"],
        )

    def test_positive_case_2_reports_missing_fields_without_generation(self):
        case = STEP_2_9_TEST_CASES[4]
        result = server.handle_mcp_request(
            {
                "jsonrpc": "2.0",
                "id": 4,
                "method": "tools/call",
                "params": {
                    "name": "apiResponseCleaner",
                    "arguments": case["input"],
                },
            }
        )
        self.assertEqual(
            result["result"]["structuredContent"],
            case["expected_output"],
        )

    def test_positive_case_3_preserves_raw_order_for_removed_fields(self):
        case = {
            "id": "TC3B",
            "type": "Positive",
            "description": "Preserve raw_response order for removed_fields.",
            "input": {
                "raw_response": {"b": 2, "a": 1, "keep": True, "c": 3},
                "target_fields": ["keep"],
            },
            "expected_output": {
                "cleaned_response": {"keep": True},
                "missing_fields": [],
                "removed_fields": ["b", "a", "c"],
            },
        }
        result = server.handle_mcp_request(
            {
                "jsonrpc": "2.0",
                "id": 5,
                "method": "tools/call",
                "params": {
                    "name": "apiResponseCleaner",
                    "arguments": case["input"],
                },
            }
        )
        self.assertEqual(
            result["result"]["structuredContent"],
            case["expected_output"],
        )

    def test_positive_case_4_empty_target_fields_is_valid_and_removes_all_fields(self):
        case = STEP_2_9_TEST_CASES[3]
        result = server.handle_mcp_request(
            {
                "jsonrpc": "2.0",
                "id": 6,
                "method": "tools/call",
                "params": {
                    "name": "apiResponseCleaner",
                    "arguments": case["input"],
                },
            }
        )
        self.assertEqual(
            result["result"]["structuredContent"],
            case["expected_output"],
        )

    def test_positive_case_5_same_input_always_returns_same_output(self):
        case = {
            "id": "TC5B",
            "type": "Positive",
            "description": "Deterministic output for repeated identical requests.",
            "input": {
                "raw_response": {"name": "Ada", "role": "admin"},
                "target_fields": ["role", "email", "name"],
            },
            "expected_output": {
                "cleaned_response": {"role": "admin", "name": "Ada"},
                "missing_fields": ["email"],
                "removed_fields": [],
            },
        }
        request = {
            "jsonrpc": "2.0",
            "id": 7,
            "method": "tools/call",
            "params": {
                "name": "apiResponseCleaner",
                "arguments": case["input"],
            },
        }
        outputs = [server.handle_mcp_request(request) for _ in range(3)]
        compact = json.dumps(
            case["expected_output"],
            ensure_ascii=True,
            separators=(",", ":"),
        )
        self.assertEqual(outputs[0], outputs[1])
        self.assertEqual(outputs[1], outputs[2])
        self.assertEqual(outputs[0]["result"]["content"][0]["text"], compact)

    def test_negative_case_1_rejects_missing_raw_response(self):
        result = server.handle_mcp_request(
            {
                "jsonrpc": "2.0",
                "id": 8,
                "method": "tools/call",
                "params": {
                    "name": "apiResponseCleaner",
                    "arguments": {"target_fields": ["name"]},
                },
            }
        )
        self.assertEqual(
            result,
            {
                "jsonrpc": "2.0",
                "id": 8,
                "error": {
                    "code": -32602,
                    "message": "The 'raw_response' field is required.",
                },
            },
        )

    def test_negative_case_2_rejects_non_object_raw_response(self):
        case = {
            "id": "TC9",
            "type": "Negative",
            "description": "Reject non-object raw_response input.",
            "input": {
                "raw_response": "not-an-object",
                "target_fields": ["name"],
            },
            "expected_error": {
                "code": -32602,
                "message": "The 'raw_response' field must be an object.",
            },
        }
        result = server.handle_mcp_request(
            {
                "jsonrpc": "2.0",
                "id": 9,
                "method": "tools/call",
                "params": {
                    "name": "apiResponseCleaner",
                    "arguments": case["input"],
                },
            }
        )
        self.assertEqual(
            result,
            {
                "jsonrpc": "2.0",
                "id": 9,
                "error": case["expected_error"],
            },
        )

    def test_negative_case_3_rejects_invalid_target_fields_entries(self):
        case = STEP_2_9_TEST_CASES[7]
        result = server.handle_mcp_request(
            {
                "jsonrpc": "2.0",
                "id": 10,
                "method": "tools/call",
                "params": {
                    "name": "apiResponseCleaner",
                    "arguments": case["input"],
                },
            }
        )
        self.assertEqual(
            result,
            {
                "jsonrpc": "2.0",
                "id": 10,
                "error": case["expected_error"],
            },
        )

    def test_negative_case_4_rejects_extra_argument_field(self):
        case = STEP_2_9_TEST_CASES[6]
        result = server.handle_mcp_request(
            {
                "jsonrpc": "2.0",
                "id": 11,
                "method": "tools/call",
                "params": {
                    "name": "apiResponseCleaner",
                    "arguments": case["input"],
                },
            }
        )
        self.assertEqual(
            result,
            {
                "jsonrpc": "2.0",
                "id": 11,
                "error": case["expected_error"],
            },
        )


if __name__ == "__main__":
    unittest.main()
