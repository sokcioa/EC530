#!/usr/bin/env python3
import os
import sys
import time
import json
import asyncio
import threading
import queue
import signal
import select
import pickle
from redis_connection import redis

class TerminalChat:
    def __init__(self):
        self.topics = []
        self.subscribed_topics = set()
        self.topic_messages = {}  # Dictionary to store messages for each topic
        self.new_messages = {}    # Dictionary to track new messages for each topic
        self.subscribers = {}     # Dictionary to store pubsub objects for each topic
        self.queue = queue.Queue()
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self.run_async_loop, daemon=True)
        self.thread.start()
        self.running = True
        self.profiles_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "profiles")
        
        # Create profiles directory if it doesn't exist
        if not os.path.exists(self.profiles_dir):
            os.makedirs(self.profiles_dir)
        
        # Set up signal handler for graceful exit
        signal.signal(signal.SIGINT, self.signal_handler)
        
        # Get username at startup
        self.username = self._get_username()
        
        # Load existing topics
        asyncio.run_coroutine_threadsafe(self._load_topics(), self.loop)
        time.sleep(1)  # Give some time for topics to load
        
    def signal_handler(self, sig, frame):
        """Handle Ctrl+C gracefully"""
        print("\nExiting gracefully...")
        self.save_profile()
        self.running = False
        sys.exit(0)
        
    def _get_username(self):
        """Get username at startup"""
        self.clear_screen()
        print("\n" + "=" * 60)
        print("Redis P2P Chat - Terminal Interface".center(60))
        print("=" * 60 + "\n")
        
        # Check for existing profiles
        profiles = self._get_existing_profiles()
        
        if profiles:
            print("Existing profiles found:")
            for i, profile in enumerate(profiles, 1):
                print(f"{i}. {profile}")
            print(f"{len(profiles) + 1}. Create new profile")
            
            try:
                choice = int(input("\nSelect a profile (or create new): "))
                if 1 <= choice <= len(profiles):
                    username = profiles[choice - 1]
                    self._load_profile(username)
                    return username
                elif choice == len(profiles) + 1:
                    # Create new profile
                    pass
                else:
                    print("Invalid choice. Creating new profile.")
            except ValueError:
                print("Invalid input. Creating new profile.")
        
        # Create new profile
        print("\nWelcome to Redis P2P Chat!")
        print("Please enter your username to continue:")
        username = input("> ").strip()
        if not username:
            username = "demo_user"
            print(f"Using default username: {username}")
        return username
    
    def _get_existing_profiles(self):
        """Get list of existing profiles"""
        profiles = []
        if os.path.exists(self.profiles_dir):
            for file in os.listdir(self.profiles_dir):
                if file.endswith(".profile"):
                    profiles.append(file[:-8])  # Remove .profile extension
        return sorted(profiles)
    
    def _load_profile(self, username):
        """Load a user profile"""
        profile_path = os.path.join(self.profiles_dir, f"{username}.profile")
        if os.path.exists(profile_path):
            try:
                with open(profile_path, 'rb') as f:
                    profile_data = pickle.load(f)
                
                # Load subscribed topics
                self.subscribed_topics = set(profile_data.get('subscribed_topics', []))
                
                # Subscribe to topics
                for topic in self.subscribed_topics:
                    asyncio.run_coroutine_threadsafe(
                        self._subscribe_to_topic(topic, username),
                        self.loop
                    )
                
                print(f"Profile loaded for user: {username}")
                print(f"Subscribed to {len(self.subscribed_topics)} topics")
                time.sleep(1)
            except Exception as e:
                print(f"Error loading profile: {str(e)}")
                print("Creating new profile instead.")
        
    def save_profile(self):
        """Save the current user profile"""
        profile_path = os.path.join(self.profiles_dir, f"{self.username}.profile")
        try:
            profile_data = {
                'username': self.username,
                'subscribed_topics': list(self.subscribed_topics),
                'last_login': time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            with open(profile_path, 'wb') as f:
                pickle.dump(profile_data, f)
            
            print(f"Profile saved for user: {self.username}")
        except Exception as e:
            print(f"Error saving profile: {str(e)}")
        
    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        
    def print_header(self):
        print("\n" + "=" * 60)
        print(f"Redis P2P Chat - Terminal Interface (User: {self.username})".center(60))
        print("=" * 60 + "\n")
        
    def print_menu(self):
        # Calculate total new messages
        total_new_messages = sum(self.new_messages.values())
        
        print("\nOptions:")
        print("1. Create Topic")
        print("2. Subscribe to Topic")
        print("3. Publish to Topic")
        if total_new_messages > 0:
            print(f"4. See Topics (\033[1;33mNew: {total_new_messages}\033[0m)")
        else:
            print("4. See Topics")
        print("5. Unsubscribe from Topic")
        print("6. Exit")
        print("\nEnter your choice (1-6): ", end="")
        
    def run(self):
        # Start a thread to check for new messages periodically
        refresh_thread = threading.Thread(target=self.refresh_loop, daemon=True)
        refresh_thread.start()
        
        while self.running:
            self.clear_screen()
            self.print_header()
            self.print_menu()
            
            # Set up non-blocking input
            if sys.stdin in select.select([sys.stdin], [], [], 1)[0]:
                choice = input()
                
                if choice == '1':
                    self.create_topic()
                elif choice == '2':
                    self.subscribe_to_topic()
                elif choice == '3':
                    self.publish_to_topic()
                elif choice == '4':
                    self.see_topics()
                elif choice == '5':
                    self.unsubscribe_from_topic()
                elif choice == '6':
                    print("\nExiting...")
                    self.save_profile()
                    self.running = False
                    sys.exit(0)
                else:
                    print("\nInvalid choice. Press Enter to continue...")
                    input()
    
    def refresh_loop(self):
        """Periodically check for new messages and update the UI"""
        while self.running:
            # Check the queue for messages from the asyncio event loop
            try:
                while True:
                    msg_type, msg = self.queue.get_nowait()
                    if msg_type == "status":
                        # Just consume the status message
                        pass
                    self.queue.task_done()
            except queue.Empty:
                pass
            
            # Sleep for a short time before checking again
            time.sleep(1)
    
    def create_topic(self):
        self.clear_screen()
        self.print_header()
        print("Create a new topic\n")
        
        topic = input("Enter topic name: ").strip()
        if not topic:
            print("\nTopic name cannot be empty. Press Enter to continue...")
            input()
            return
            
        message = input("Enter first message: ").strip()
        if not message:
            print("\nMessage cannot be empty. Press Enter to continue...")
            input()
            return
            
        # Use the username set at startup
        user_id = self.username
        
        # Add the topic to the list if it doesn't exist
        if topic not in self.topics:
            self.topics.append(topic)
            self.topic_messages[topic] = []
            self.new_messages[topic] = 0
        
        # Publish the message
        asyncio.run_coroutine_threadsafe(
            self._publish_message(topic, message, user_id),
            self.loop
        )
        
        print(f"\nTopic '{topic}' created with your message. Press Enter to continue...")
        input()
    
    def subscribe_to_topic(self):
        self.clear_screen()
        self.print_header()
        print("Subscribe to a topic\n")
        
        if not self.topics:
            print("No topics available. Create a topic first.")
            print("\nPress Enter to continue...")
            input()
            return
            
        print("Available topics:")
        for i, topic in enumerate(self.topics, 1):
            if topic not in self.subscribed_topics:
                print(f"{i}. {topic}")
        
        try:
            choice = int(input("\nEnter topic number: "))
            if choice < 1 or choice > len(self.topics):
                print("\nInvalid topic number. Press Enter to continue...")
                input()
                return
                
            topic = self.topics[choice-1]
            if topic in self.subscribed_topics:
                print(f"\nYou are already subscribed to '{topic}'. Press Enter to continue...")
                input()
                return
                
            # Use the username set at startup
            user_id = self.username
            
            # Subscribe to the topic
            asyncio.run_coroutine_threadsafe(
                self._subscribe_to_topic(topic, user_id),
                self.loop
            )
            
            print(f"\nSubscribed to topic '{topic}'. Press Enter to continue...")
            input()
        except ValueError:
            print("\nInvalid input. Press Enter to continue...")
            input()
    
    def publish_to_topic(self):
        self.clear_screen()
        self.print_header()
        print("Publish to a topic\n")
        
        if not self.topics:
            print("No topics available. Create a topic first.")
            print("\nPress Enter to continue...")
            input()
            return
            
        print("Available topics:")
        for i, topic in enumerate(self.topics, 1):
            print(f"{i}. {topic}")
        
        try:
            choice = int(input("\nEnter topic number: "))
            if choice < 1 or choice > len(self.topics):
                print("\nInvalid topic number. Press Enter to continue...")
                input()
                return
                
            topic = self.topics[choice-1]
            message = input("Enter your message: ").strip()
            if not message:
                print("\nMessage cannot be empty. Press Enter to continue...")
                input()
                return
                
            # Use the username set at startup
            user_id = self.username
            
            # Publish the message
            asyncio.run_coroutine_threadsafe(
                self._publish_message(topic, message, user_id),
                self.loop
            )
            
            print(f"\nMessage published to topic '{topic}'. Press Enter to continue...")
            input()
        except ValueError:
            print("\nInvalid input. Press Enter to continue...")
            input()
    
    def see_topics(self):
        self.clear_screen()
        self.print_header()
        print("View topics and their messages\n")
        
        # Filter to show only subscribed topics
        subscribed_topics = [topic for topic in self.topics if topic in self.subscribed_topics]
        
        if not subscribed_topics:
            print("You are not subscribed to any topics. Subscribe to a topic first.")
            print("\nPress Enter to continue...")
            input()
            return
            
        # Check if there are any new messages
        has_new_messages = any(self.new_messages.get(topic, 0) > 0 for topic in subscribed_topics)
        if has_new_messages:
            print("\033[1;33m*** NEW MESSAGES AVAILABLE ***\033[0m")
        
        print("\nYour subscribed topics:")
        for i, topic in enumerate(subscribed_topics, 1):
            new_count = self.new_messages.get(topic, 0)
            if new_count > 0:
                print(f"{i}. \033[1;32m{topic}\033[0m (\033[1;33mNew: {new_count}\033[0m)")
            else:
                print(f"{i}. {topic}")
        
        try:
            choice = int(input("\nEnter topic number to view messages (0 to go back): "))
            if choice == 0:
                return
            if choice < 1 or choice > len(subscribed_topics):
                print("\nInvalid topic number. Press Enter to continue...")
                input()
                return
                
            topic = subscribed_topics[choice-1]
            
            self.clear_screen()
            self.print_header()
            print(f"Messages in topic '{topic}'\n")
            
            # Load all messages from Redis for this topic
            asyncio.run_coroutine_threadsafe(
                self._load_topic_messages(topic),
                self.loop
            )
            
            # Wait a moment for messages to load
            time.sleep(0.5)
            
            if topic in self.topic_messages and self.topic_messages[topic]:
                for msg in self.topic_messages[topic]:
                    # Highlight new messages from other users
                    is_new = False
                    if topic in self.new_messages and self.new_messages[topic] > 0 and msg['user'] != self.username:
                        is_new = True
                    
                    # Highlight messages sent by the current user
                    is_own = msg['user'] == self.username
                    
                    if is_new:
                        print("\033[1;33m", end="")  # Yellow for new messages
                    elif is_own:
                        print("\033[1;36m", end="")  # Cyan for own messages
                    
                    print(f"From: {msg['user']}")
                    print(f"Content: {msg['content']}")
                    print(f"Time: {msg['timestamp']}")
                    print("-" * 50)
                    
                    if is_new or is_own:
                        print("\033[0m", end="")  # Reset color
            else:
                print("No messages in this topic yet.")
            
            # Reset the new message counter
            if topic in self.new_messages:
                self.new_messages[topic] = 0
                
            print("\nPress Enter to continue...")
            input()
        except ValueError:
            print("\nInvalid input. Press Enter to continue...")
            input()
    
    def unsubscribe_from_topic(self):
        self.clear_screen()
        self.print_header()
        print("Unsubscribe from a topic\n")
        
        # Filter to show only subscribed topics
        subscribed_topics = [topic for topic in self.topics if topic in self.subscribed_topics]
        
        if not subscribed_topics:
            print("You are not subscribed to any topics.")
            print("\nPress Enter to continue...")
            input()
            return
            
        print("Your subscribed topics:")
        for i, topic in enumerate(subscribed_topics, 1):
            print(f"{i}. {topic}")
        
        try:
            choice = int(input("\nEnter topic number to unsubscribe (0 to go back): "))
            if choice == 0:
                return
            if choice < 1 or choice > len(subscribed_topics):
                print("\nInvalid topic number. Press Enter to continue...")
                input()
                return
                
            topic = subscribed_topics[choice-1]
            
            # Unsubscribe from the topic
            asyncio.run_coroutine_threadsafe(
                self._unsubscribe_from_topic(topic),
                self.loop
            )
            
            print(f"\nUnsubscribed from topic '{topic}'. Press Enter to continue...")
            input()
        except ValueError:
            print("\nInvalid input. Press Enter to continue...")
            input()
            
    async def _unsubscribe_from_topic(self, topic):
        """Unsubscribe from a topic"""
        if topic in self.subscribers:
            # Unsubscribe from the topic
            pubsub = self.subscribers[topic]
            await pubsub.unsubscribe(topic)
            
            # Remove the topic from subscribed topics
            self.subscribed_topics.remove(topic)
            
            # Remove the subscriber from Redis
            sub_key = f"topic:{topic}:subscribers"
            await redis.srem(sub_key, self.username)
            
            # Update the status
            self.queue.put(("status", f"Unsubscribed from topic '{topic}'"))
    
    async def _load_topics(self):
        """Load existing topics from Redis"""
        # Get all keys that match the pattern "topic:*:publishers"
        keys = await redis.keys("topic:*:publishers")
        for key in keys:
            # Extract the topic name from the key
            topic = key.split(":")[1]
            if topic not in self.topics:
                self.topics.append(topic)
                self.topic_messages[topic] = []
                self.new_messages[topic] = 0
    
    async def _publish_message(self, topic, message, user_id):
        """Publish a message to a topic"""
        # First, ensure the user has permission to publish
        pub_key = f"topic:{topic}:publishers"
        await redis.sadd(pub_key, user_id)
        
        # Create the message
        msg = {
            "content": message,
            "user": user_id,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Publish the message
        await redis.publish(topic, json.dumps(msg))
        
        # Store the message in Redis for history
        messages_key = f"topic:{topic}:messages"
        await redis.rpush(messages_key, json.dumps(msg))
        
        # Add the message to the topic's message list
        if topic not in self.topic_messages:
            self.topic_messages[topic] = []
        self.topic_messages[topic].append(msg)
        
        # Update the status
        self.queue.put(("status", f"Message published to topic '{topic}'"))
    
    async def _subscribe_to_topic(self, topic, user_id):
        """Subscribe to a topic"""
        # First, ensure the user has permission to subscribe
        sub_key = f"topic:{topic}:subscribers"
        await redis.sadd(sub_key, user_id)
        
        # Add the topic to the subscribed topics
        self.subscribed_topics.add(topic)
        
        # Create a pubsub instance for this topic
        pubsub = redis.pubsub()
        await pubsub.subscribe(topic)
        self.subscribers[topic] = pubsub
        
        # Start a task to listen for messages
        asyncio.create_task(self._listen_for_messages(topic))
        
        # Update the status
        self.queue.put(("status", f"Subscribed to topic '{topic}'"))
    
    async def _listen_for_messages(self, topic):
        """Listen for messages on a topic"""
        pubsub = self.subscribers[topic]
        
        try:
            while True:
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if message:
                    try:
                        data = json.loads(message['data'])
                        
                        # Add the message to the topic's message list
                        if topic not in self.topic_messages:
                            self.topic_messages[topic] = []
                        self.topic_messages[topic].append(data)
                        
                        # Only increment the new message counter if the message is from another user
                        if data['user'] != self.username:
                            if topic not in self.new_messages:
                                self.new_messages[topic] = 0
                            self.new_messages[topic] += 1
                            
                            # Update the status
                            self.queue.put(("status", f"New message in topic '{topic}' from {data['user']}"))
                    except json.JSONDecodeError:
                        print(f"Error decoding message: {message['data']}")
                await asyncio.sleep(0.1)
        except Exception as e:
            print(f"Error in _listen_for_messages: {str(e)}")
    
    async def _load_topic_messages(self, topic):
        """Load all messages for a topic from Redis"""
        # Get all messages for this topic from Redis
        messages_key = f"topic:{topic}:messages"
        messages = await redis.lrange(messages_key, 0, -1)
        
        # Clear existing messages for this topic
        self.topic_messages[topic] = []
        
        # Add messages to the topic's message list
        for msg_json in messages:
            try:
                msg = json.loads(msg_json)
                self.topic_messages[topic].append(msg)
            except json.JSONDecodeError:
                print(f"Error decoding message: {msg_json}")
    
    def run_async_loop(self):
        """Run the asyncio event loop in a separate thread"""
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

if __name__ == "__main__":
    chat = TerminalChat()
    chat.run() 