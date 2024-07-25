import customtkinter as ctk
import tkinter as tk
import threading
import time
from tkinter import messagebox

class ElasticsearchQueryBuilderTab(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.create_widgets()
        self.nodes = []
        self.links = []
        self.dragging = False
        self.drag_data = {"x": 0, "y": 0, "item": None}

    def create_widgets(self):
        # Left panel for query buttons
        self.left_panel = ctk.CTkFrame(self)
        self.left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

        # Add query buttons
        queries = ["Match", "Term", "Range", "Bool", "Must", "Should", "Must Not"]
        for query in queries:
            btn = ctk.CTkButton(self.left_panel, text=query, command=lambda q=query: self.create_node(q))
            btn.pack(pady=5)

        # Right panel for flowchart
        self.right_panel = ctk.CTkFrame(self)
        self.right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Canvas for flowchart
        self.canvas = tk.Canvas(self.right_panel, bg="white")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Bind mouse events
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)

    def create_node(self, query_type):
        x, y = 50, 50  # Default position
        node = self.canvas.create_rectangle(x, y, x+100, y+30, fill="lightblue", outline="black")
        text = self.canvas.create_text(x+50, y+15, text=query_type)
        self.nodes.append((node, text))

    def on_press(self, event):
        item = self.canvas.find_closest(event.x, event.y)[0]
        if item in [node[0] for node in self.nodes]:
            self.dragging = True
            self.drag_data["item"] = item
            self.drag_data["x"] = event.x
            self.drag_data["y"] = event.y

    def on_drag(self, event):
        if self.dragging:
            dx = event.x - self.drag_data["x"]
            dy = event.y - self.drag_data["y"]
            self.canvas.move(self.drag_data["item"], dx, dy)
            for node, text in self.nodes:
                if node == self.drag_data["item"]:
                    self.canvas.move(text, dx, dy)
                    break
            self.drag_data["x"] = event.x
            self.drag_data["y"] = event.y
            self.update_links()

    def on_release(self, event):
        if self.dragging:
            self.dragging = False
        else:
            self.try_create_link(event)

    def update_links(self):
        for link in self.links:
            self.canvas.delete(link)
        self.links.clear()
        for i, (node1, _) in enumerate(self.nodes):
            for node2, _ in self.nodes[i+1:]:
                x1, y1, _, _ = self.canvas.coords(node1)
                x2, y2, _, _ = self.canvas.coords(node2)
                link = self.canvas.create_line(x1+50, y1+30, x2+50, y2, arrow=tk.LAST)
                self.links.append(link)

    def try_create_link(self, event):
        item = self.canvas.find_closest(event.x, event.y)[0]
        if item in [node[0] for node in self.nodes]:
            if not hasattr(self, 'link_start'):
                self.link_start = item
            else:
                if self.link_start != item:
                    x1, y1, _, _ = self.canvas.coords(self.link_start)
                    x2, y2, _, _ = self.canvas.coords(item)
                    link = self.canvas.create_line(x1+50, y1+30, x2+50, y2, arrow=tk.LAST)
                    self.links.append(link)
                delattr(self, 'link_start')

class ButtonsEntryTab(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.create_widgets()

    def create_widgets(self):
        ctk.CTkButton(self, text="Standard Button").pack(pady=5)
        ctk.CTkButton(self, text="Rounded Button", corner_radius=20).pack(pady=5)
        
        entry_frame = ctk.CTkFrame(self)
        entry_frame.pack(pady=10)
        self.entry = ctk.CTkEntry(entry_frame, placeholder_text="Enter text here")
        self.entry.pack(side=tk.LEFT, padx=5)
        ctk.CTkButton(entry_frame, text="Submit", command=self.submit_entry).pack(side=tk.LEFT, padx=5)

    def submit_entry(self):
        print(f"Submitted: {self.entry.get()}")
        self.entry.delete(0, tk.END)

class SlidersSwitchesTab(ctk.CTkFrame):
    def __init__(self, parent, toggle_mode_callback):
        super().__init__(parent)
        self.toggle_mode_callback = toggle_mode_callback
        self.create_widgets()

    def create_widgets(self):
        self.slider = ctk.CTkSlider(self, from_=0, to=100, number_of_steps=10)
        self.slider.pack(pady=10)
        self.slider_label = ctk.CTkLabel(self, text="Slider Value: 0")
        self.slider_label.pack()
        self.slider.configure(command=self.update_slider_label)

        self.switch = ctk.CTkSwitch(self, text="Dark Mode", command=self.toggle_mode)
        self.switch.pack(pady=10)
        self.switch.select()

    def update_slider_label(self, value):
        self.slider_label.configure(text=f"Slider Value: {int(value)}")

    def toggle_mode(self):
        self.toggle_mode_callback()

class ProgressTextTab(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.create_widgets()

    def create_widgets(self):
        self.progress = ctk.CTkProgressBar(self)
        self.progress.pack(pady=10)
        self.progress.set(0)

        ctk.CTkButton(self, text="Start Progress", command=self.start_progress).pack(pady=5)

        self.textbox = ctk.CTkTextbox(self, height=100)
        self.textbox.pack(pady=10, fill=tk.X)
        self.textbox.insert("0.0", "This is a customtkinter textbox.\nYou can add multiple lines of text here.")

    def start_progress(self):
        def progress_thread():
            for i in range(101):
                self.progress.set(i / 100)
                self.update_idletasks()
                self.after(20)
        threading.Thread(target=progress_thread).start()

class ChatWindowTab(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.create_widgets()

    def create_widgets(self):
        self.chat_display = ctk.CTkTextbox(self, height=300, width=500, state="disabled")
        self.chat_display.pack(pady=(10, 5), padx=10, fill=tk.BOTH, expand=True)

        input_frame = ctk.CTkFrame(self)
        input_frame.pack(pady=(5, 10), padx=10, fill=tk.X)

        self.chat_input = ctk.CTkEntry(input_frame, placeholder_text="Type your message here...", width=1000)
        self.chat_input.pack(side=tk.LEFT, padx=(0, 10), fill=tk.X, expand=True)

        send_button = ctk.CTkButton(input_frame, text="Send", width=80, command=self.send_message)
        send_button.pack(side=tk.RIGHT)

        self.chat_input.bind("<Return>", lambda event: self.send_message())

    def send_message(self):
        user_message = self.chat_input.get().strip()
        if user_message:
            self.display_message("You", user_message)
            self.chat_input.delete(0, tk.END)
            threading.Thread(target=self.stream_response).start()

    def stream_response(self):
        response = "Thank you for your message. This is a streamed response."
        self.chat_display.configure(state="normal")
        self.chat_display.insert(tk.END, "Bot: ")
        self.chat_display.configure(state="disabled")
        
        for char in response:
            time.sleep(0.05)  # Adjust this value to change the streaming speed
            self.chat_display.configure(state="normal")
            self.chat_display.insert(tk.END, char)
            self.chat_display.see(tk.END)
            self.chat_display.configure(state="disabled")
            self.update_idletasks()
        
        self.chat_display.configure(state="normal")
        self.chat_display.insert(tk.END, "\n\n")
        self.chat_display.configure(state="disabled")

    def display_message(self, sender, message):
        self.chat_display.configure(state="normal")
        self.chat_display.insert(tk.END, f"{sender}: {message}\n\n")
        self.chat_display.see(tk.END)
        self.chat_display.configure(state="disabled")

class IntroApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("CustomTkinter Intro")
        self.geometry("600x500")

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        self.title_label = ctk.CTkLabel(self.main_frame, text="Welcome to CustomTkinter", font=ctk.CTkFont(size=24, weight="bold"))
        self.title_label.pack(pady=10)

        self.tabview = ctk.CTkTabview(self.main_frame)
        self.tabview.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.add_tab("Buttons & Entry", ButtonsEntryTab)
        self.add_tab("Sliders & Switches", SlidersSwitchesTab, toggle_mode_callback=self.toggle_mode)
        self.add_tab("Progress & Text", ProgressTextTab)
        self.add_tab("Chatwindow", ChatWindowTab)
        self.add_tab("Elasticsearch Query Builder", ElasticsearchQueryBuilderTab)

    def add_tab(self, name, tab_class, **kwargs):
        tab = self.tabview.add(name)
        tab_instance = tab_class(tab, **kwargs)
        tab_instance.pack(fill=tk.BOTH, expand=True)

    def toggle_mode(self):
        new_mode = "light" if ctk.get_appearance_mode() == "dark" else "dark"
        ctk.set_appearance_mode(new_mode)

if __name__ == "__main__":
    app = IntroApp()
    app.mainloop()