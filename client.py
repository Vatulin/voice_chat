import socket
import threading
import pyaudio
import tkinter as tk
from tkinter import ttk, messagebox

class VoiceClient:
    def __init__(self, host='localhost', port=12345):
        self.host = host
        self.port = port
        self.connected = False
        self.recording = False

        """Настройки аудио"""
        self.chunk_size = 1024
        self.audio_format = pyaudio.paInt16
        self.channels = 1
        self.rate = 44100
        
        self.audio = pyaudio.PyAudio()

        """Создаем GUI"""
        self.create_gui()

    def create_gui(self):
        """Создание графического интерфейса"""
        self.root = tk.Tk()
        self.root.title("Голосовой чат")
        self.root.geometry("400x200")
        self.root.resizable(False, False)
    
        """Фрейм для подключения"""
        connection_frame = ttk.Frame(self.root, padding="10")
        connection_frame.grid(row=0, column=0, sticky=(tk.W, tk.E))
        ttk.Label(connection_frame, text="Порт").grid(row=0, column=2, sticky=tk.W, padx=(10,0))
        self.port_entry = ttk.Entry(connection_frame, width=10)
        self.port_entry.insert(0, str(self.port))
        self.port_entry.grid(row=0, column=3, padx=5)

        ttk.Label(connection_frame, text="IP сервера:").grid(row=0, column=0, sticky=tk.W)
        self.host_entry = ttk.Entry(connection_frame, width=15)
        self.host_entry.insert(0, self.host)
        self.host_entry.grid(row=0, column=1, padx=5)

        self.connect_button = ttk.Button(
            connection_frame, 
            text="Подключиться",
            command=self.toggle_connection
        )
        self.connect_button.grid(row=0, column=4, padx=10)

        """Фрейм статуса"""
        status_frame = ttk.Frame(self.root, padding="10")
        status_frame.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        self.status_label = ttk.Label(status_frame, text="Статус: Не подключено", foreground="red")
        self.status_label.grid(row=0, column=0, sticky=tk.W)

        """Фрейм управления"""
        control_frame = ttk.Frame(self.root, padding="10")
        control_frame.grid(row=2, column=0, sticky=(tk.W, tk.E))
        
        self.record_button = ttk.Button(
            control_frame,
            text="Начать разговор",
            command=self.toggle_recording,
            state="disabled"
        )
        self.record_button.grid(row=0, column=0, pady=10)

        """Информация"""
        info_frame = ttk.Frame(self.root, padding="10")
        info_frame.grid(row=3, column=0, sticky=(tk.W, tk.E))
        
        info_text = "Подключитесь к серверу и нажмите 'Начать разговор' для общения"
        ttk.Label(info_frame, text=info_text, wraplength=380, justify=tk.CENTER).grid(row=0, column=0)

        """Настройка расширения"""
        self.root.columnconfigure(0, weight=1)

    def toggle_connection(self):
        """Подключение/отключение от сервера"""
        if not self.connected:
            self.connect_to_server()
        else:
            self.disconnect_from_server()
    
    def connect_to_server(self):
        """Подключение к серверу"""
        try:
            self.host = self.host_entry.get()
            self.port = int(self.port_entry.get())

            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))

            self.connected = True
            self.status_label.config(text="Статус: Подключено", foreground="green")
            self.connect_button.config(text="Отключиться")
            self.record_button.config(state="normal")

            """Запускаем поток для приема аудио"""
            self.receive_thread = threading.Thread(target=self.receive_audio)
            self.receive_thread.daemon = True
            self.receive_thread.start()

            messagebox.showinfo("Успех", "Успешно подключено к серверу!")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось подключиться: {e}")
        
    def disconnect_from_server(self):
        """Отключение от сервера"""
        if self.recording:
            self.stop_recording()

        self.connected = False

        if hasattr(self, 'socket'):
            try:
                self.socket.close()
            except:
                pass
        
        self.status_label.config(text="Статус: Не подключено", foreground="red")
        self.connect_button.config(text="Подключиться")
        self.record_button.config(state="disabled")
    
    def toggle_recording(self):
        """Начать/остановить передачу голоса"""
        if not self.recording:
            self.start_recording()
        else:
            self.stop_recording()
    
    def start_recording(self):
        """Начать запись и передачу голоса"""
        try:
            """Открываем поток для записи"""
            self.input_stream = self.audio.open(
                format=self.audio_format,
            channels=self.channels,
            rate=self.rate,
            input=True,
            frames_per_buffer=self.chunk_size
            )

            """Открываем поток для воспроизведения"""
            self.output_stream = self.audio.open(
            format=self.audio_format,
            channels=self.channels,
            rate=self.rate,
            output=True,
            frames_per_buffer=self.chunk_size
        )
        
            self.recording = True
            self.record_button.config(text="Остановить разговор")

            """Запускаем поток для отправки аудио"""
            self.send_thread = threading.Thread(target=self.send_audio)
            self.send_thread.daemon = True
            self.send_thread.start()
        
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось начать запись: {e}")
    def stop_recording(self):
        """Остановить запись и передачу голоса"""
        self.recording = False

        if hasattr(self, 'input_stream'):
            self.input_stream.stop_stream()
            self.input_stream.close()
        
        if hasattr(self, 'output_stream'):
            self.output_stream.stop_stream()
            self.output_stream.close()
        
        self.record_button.config(text="Начать разговор")
    
    def send_audio(self):
        """Отправка аудио данных на сервер"""
        while self.recording and self.connected:
            try:
                data = self.input_stream.read(self.chunk_size, exception_on_overflow=False)
                self.socket.send(data)
            except Exception as e:
                if self.connected:
                    print(f"Ошибка отправки: {e}")
                break
    
    def receive_audio(self):
        """Прием аудио данных от сервера"""
        while self.connected:
            try:
                data = self.socket.recv(4096)
                if not data:
                    break
                
                """Воспроизводим полученные данные"""
                if hasattr(self, 'output_stream') and self.recording:
                    self.output_stream.write(data)
            
            except Exception as e:
                if self.connected:
                    print(f"Ошибка приема: {e}")
                break
        
        if self.connected:
            self.root.after(0, self.disconnect_from_server)
    
    def run(self):
        """Запуск клиента"""
        try:
            self.root.mainloop()
        finally:
            if self.connected:
                self.disconnect_from_server()
            self.audio.terminate()

if __name__=="__main__":
    client = VoiceClient()
    client.run()