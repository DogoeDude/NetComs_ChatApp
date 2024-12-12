import unittest
from protocol import (
    MessageType, 
    create_message, 
    parse_message, 
    format_message_for_display,
    create_handshake_message
)
import json
from datetime import datetime

class TestProtocol(unittest.TestCase):
    def setUp(self):
        self.username = "TestUser"
        self.content = "Hello, World!"
        self.timestamp = "12:00:00"

    def test_create_message(self):
        """Test message creation for different message types"""
        # Test chat message
        chat_msg = create_message(MessageType.CHAT, self.username, self.content, self.timestamp)
        chat_data = json.loads(chat_msg.decode('utf-8'))
        
        self.assertEqual(chat_data['type'], MessageType.CHAT.value)
        self.assertEqual(chat_data['username'], self.username)
        self.assertEqual(chat_data['content'], self.content)
        self.assertEqual(chat_data['timestamp'], self.timestamp)

        # Test system message
        sys_msg = create_message(MessageType.SYSTEM, "System", "User joined", self.timestamp)
        sys_data = json.loads(sys_msg.decode('utf-8'))
        
        self.assertEqual(sys_data['type'], MessageType.SYSTEM.value)
        self.assertEqual(sys_data['username'], "System")

    def test_parse_message(self):
        """Test message parsing"""
        original_msg = create_message(MessageType.CHAT, self.username, self.content, self.timestamp)
        parsed_msg = parse_message(original_msg)
        
        self.assertIsInstance(parsed_msg, dict)
        self.assertEqual(parsed_msg['type'], MessageType.CHAT.value)
        self.assertEqual(parsed_msg['username'], self.username)
        self.assertEqual(parsed_msg['content'], self.content)

    def test_format_message_for_display(self):
        """Test message formatting for display"""
        # Test chat message formatting
        chat_data = {
            'type': MessageType.CHAT.value,
            'username': self.username,
            'content': self.content,
            'timestamp': self.timestamp
        }
        formatted_chat = format_message_for_display(chat_data)
        expected_chat = f"[{self.timestamp}] {self.username}: {self.content}"
        self.assertEqual(formatted_chat, expected_chat)

        # Test system message formatting
        sys_data = {
            'type': MessageType.SYSTEM.value,
            'username': 'System',
            'content': 'User joined',
            'timestamp': self.timestamp
        }
        formatted_sys = format_message_for_display(sys_data)
        expected_sys = f"[{self.timestamp}] System: User joined"
        self.assertEqual(formatted_sys, expected_sys)

    def test_handshake_messages(self):
        """Test handshake message creation"""
        # Test HELLO message
        hello_msg = create_handshake_message(MessageType.HELLO)
        hello_data = json.loads(hello_msg.decode('utf-8'))
        
        self.assertEqual(hello_data['type'], MessageType.HELLO.value)
        self.assertEqual(hello_data['content'], "HELLO")

        # Test HELLO_ACK message
        ack_msg = create_handshake_message(MessageType.HELLO_ACK)
        ack_data = json.loads(ack_msg.decode('utf-8'))
        
        self.assertEqual(ack_data['type'], MessageType.HELLO_ACK.value)
        self.assertEqual(ack_data['content'], "HELLO_ACK")

    def test_message_timestamps(self):
        """Test automatic timestamp generation"""
        msg = create_message(MessageType.CHAT, self.username, self.content)
        data = json.loads(msg.decode('utf-8'))
        
        # Check if timestamp is in correct format
        try:
            datetime.strptime(data['timestamp'], '%H:%M:%S')
        except ValueError:
            self.fail("Timestamp is not in correct format")

    def test_invalid_message_handling(self):
        """Test handling of invalid messages"""
        # Test with invalid JSON
        with self.assertRaises(json.JSONDecodeError):
            parse_message(b'invalid json')

        # Test with missing required fields
        invalid_msg = json.dumps({'type': 'chat'}).encode('utf-8')
        parsed = parse_message(invalid_msg)
        with self.assertRaises(KeyError):
            format_message_for_display(parsed)

if __name__ == '__main__':
    unittest.main() 