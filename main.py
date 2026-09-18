import os
import json
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.utils import get_color_from_hex

try:
    from plyer import speech_to_text
    from plyer import tts
    PLYER_AVAILABLE = True
except ImportError:
    PLYER_AVAILABLE = False

class ChatMessage(BoxLayout):
    """Ek chat sandesh ke liye ek widget."""
    def __init__(self, sender, message, **kwargs):
        super(ChatMessage, self).__init__(**kwargs)
        self.orientation = 'horizontal'
        self.padding = [10, 5]
        self.spacing = 10
        self.size_hint_y = None
        self.height = self.minimum_height

        if sender == 'bot':
            # Bot ke sandesh left-aligned honge
            halign = 'left'
            bg_color = get_color_from_hex('#E0E0E0') # Halka grey
            text_color = get_color_from_hex('#000000') # Kaala
            pos_hint = {'x': 0}
        else:
            # User ke sandesh right-aligned honge
            halign = 'right'
            bg_color = get_color_from_hex('#DCF8C6') # Halka hara
            text_color = get_color_from_hex('#000000') # Kaala
            pos_hint = {'right': 1}

        bubble = BoxLayout(orientation='vertical', size_hint=(None, None), width=self.width*0.7, pos_hint=pos_hint)
        bubble.bind(minimum_height=bubble.setter('height'))

        with bubble.canvas.before:
            from kivy.graphics import Color, RoundedRectangle
            Color(rgba=bg_color)
            self.rect = RoundedRectangle(size=bubble.size, pos=bubble.pos, radius=[15, 15, 15, 15])

        def update_rect(instance, value):
            self.rect.pos = instance.pos
            self.rect.size = instance.size

        bubble.bind(pos=update_rect, size=update_rect)

        msg_label = Label(
            text=message,
            text_size=(bubble.width * 0.9, None),
            size_hint=(1, None),
            halign=halign,
            valign='top',
            padding=(15, 10),
            color=text_color,
            font_name='Roboto' # Android par behtar dikhne ke liye
        )
        msg_label.bind(texture_size=msg_label.setter('size'))
        bubble.add_widget(msg_label)
        
        # Bubble ko left ya right align karne ke liye spacer add karein
        if sender == 'bot':
            self.add_widget(bubble)
            self.add_widget(BoxLayout(size_hint_x=0.3))
        else:
            self.add_widget(BoxLayout(size_hint_x=0.3))
            self.add_widget(bubble)

class HindiGptChatApp(App):
    def build(self):
        self.title = 'हिंदी GPT चैट'
        self.chat_history = []
        self.storage_path = os.path.join(self.user_data_dir, 'chat_history.json')

        # Mukhya layout
        main_layout = BoxLayout(orientation='vertical')

        # Chat ka itihas dikhane ke liye ScrollView
        self.chat_view = ScrollView(size_hint=(1, 1))
        self.chat_logs = BoxLayout(orientation='vertical', size_hint_y=None, spacing=10, padding=10)
        self.chat_logs.bind(minimum_height=self.chat_logs.setter('height'))
        self.chat_view.add_widget(self.chat_logs)

        main_layout.add_widget(self.chat_view)

        # Niche ka input bar
        input_layout = BoxLayout(orientation='horizontal', size_hint=(1, None), height='50dp', padding=5, spacing=10)

        self.text_input = TextInput(
            hint_text='संदेश लिखें...',
            size_hint=(1, None),
            height='48dp',
            multiline=False,
            on_text_validate=self.send_message
        )

        mic_button = Button(
            text='🎤',
            size_hint=(None, None),
            size=('48dp', '48dp'),
            on_press=self.listen_speech
        )

        send_button = Button(
            text='भेजें',
            size_hint=(None, None),
            size=('80dp', '48dp'),
            on_press=self.send_message
        )

        input_layout.add_widget(self.text_input)
        if PLYER_AVAILABLE:
            input_layout.add_widget(mic_button)
        input_layout.add_widget(send_button)

        main_layout.add_widget(input_layout)

        Window.softinput_mode = 'below_target' # Keyboard ko text input ke niche rakhe

        return main_layout

    def on_start(self):
        self.load_chat_history()

    def on_stop(self):
        self.save_chat_history()

    def send_message(self, instance):
        message_text = self.text_input.text.strip()
        if message_text:
            # User ka sandesh UI mein jodein
            self.add_message('user', message_text)
            self.text_input.text = ''
            # Bot ka jawab paane ke liye schedule karein
            Clock.schedule_once(lambda dt: self.get_bot_response(message_text), 0.5)

    def listen_speech(self, instance):
        if not PLYER_AVAILABLE:
            self.add_message('bot', 'माफ़ कीजिए, वॉयस इनपुट के लिए Plyer मॉड्यूल उपलब्ध नहीं है।')
            return
        try:
            # Bhashan se text prapt karne ka prayas karein
            result = speech_to_text.start_listening()
            # Safal hone par, text input mein daalein
            if result:
                self.text_input.text = result[0]
        except Exception as e:
            # Asafal hone par, bot ke roop mein ek sandesh dikhayein
            print(f'Speech-to-text error: {e}')
            self.add_message('bot', 'वॉयस इनपुट विफल रहा। कृपया टाइप करें।')

    def add_message(self, sender, message):
        chat_message_widget = ChatMessage(sender=sender, message=message)
        self.chat_logs.add_widget(chat_message_widget)
        # Scroll ko niche tak le jayein
        Clock.schedule_once(lambda dt: setattr(self.chat_view, 'scroll_y', 0), 0.1)
        # Itihas mein jodein
        self.chat_history.append({'sender': sender, 'text': message})

    def get_bot_response(self, user_message):
        """GPT-4 ka anukaran karne wala ek saral bot."""
        msg = user_message.lower()
        response = 'मुझे क्षमा करें, मैं यह समझ नहीं पाया। क्या आप कृपया अपना प्रश्न दूसरे तरीके से पूछ सकते हैं?' # Default jawab

        if 'नमस्ते' in msg or 'हेलो' in msg or 'hi' in msg:
            response = 'नमस्ते! मैं आपकी क्या मदद कर सकता हूँ?'
        elif 'कैसे हो' in msg or 'kya haal hai' in msg:
            response = 'मैं एक AI हूँ, मैं हमेशा सीखने की प्रक्रिया में रहता हूँ। आप बताएं, मैं आपकी कैसे सहायता कर सकता हूँ?'
        elif 'नाम क्या है' in msg or 'tumhara naam' in msg:
            response = 'मेरा नाम GPT चैटबॉट है। मैं आपकी सहायता के लिए यहाँ हूँ।'
        elif 'धन्यवाद' in msg or 'thank you' in msg:
            response = 'आपका स्वागत है! अगर आपका कोई और सवाल है तो आप पूछ सकते हैं।'
        elif 'यह ऐप' in msg or 'app ke bare me' in msg:
            response = 'यह ऐप Python और Kivy फ्रेमवर्क का उपयोग करके बनाया गया एक सरल चैट एप्लिकेशन है।'
        elif 'आप कौन हैं' in msg or 'who are you' in msg:
            response = 'मैं एक कृत्रिम बुद्धिमत्ता (AI) हूँ जिसे आपके सवालों का जवाब देने के लिए डिज़ाइन किया गया है।'

        self.add_message('bot', response)
    
    def load_chat_history(self):
        """JSON file se chat ka itihas load karein."""
        try:
            if os.path.exists(self.storage_path):
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    self.chat_history = json.load(f)
                for message in self.chat_history:
                    # Yahan widget ko સીધા add karein, 'add_message' ka upyog na karein taaki dobara save na ho
                    chat_message_widget = ChatMessage(sender=message['sender'], message=message['text'])
                    self.chat_logs.add_widget(chat_message_widget)
                Clock.schedule_once(lambda dt: setattr(self.chat_view, 'scroll_y', 0), 0.2)
        except Exception as e:
            print(f'Error loading chat history: {e}')
            self.chat_history = []

    def save_chat_history(self):
        """Chat ke itihas ko ek JSON file mein save karein."""
        try:
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(self.chat_history, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f'Error saving chat history: {e}')

if __name__ == '__main__':
    HindiGptChatApp().run()