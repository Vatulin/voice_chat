import socket
import threading
import pyaudio
import select
import time

class VoiceServer:
    def __init__(self, host='localhost', port=12345):
        self.host = host
        self.port = port
        self.clients = []
        self.running = False

        self.chunk_size = 1024
        self.audio_format = pyaudio.paInt16
        self.channels = 1
        self.rate = 44100

        self.audio = pyaudio.PyAudio()

    def start_server(self):
        """Запуск сервера"""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)

        self.running = True
        print(f"Сервер запущен на {self.host}:{self.port}")

        """Поток для принятия новых клиентов"""
        accept_thread = threading.Thread(target=self.accept_clients)
        accept_thread.daemon = True
        accept_thread.start()

        """Поток для управления сервером"""
        self.control_thread()

    def accept_clients(self):
        """Принятие новых подключений"""
        while self.running:
            try:
                client_socket, address = self.server_socket.accept()
                print(f"Новое подключение: {address}")

                """Создание отдельного потока для каждого клиента"""
                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, address)
                )
                client_thread.daemon = True
                client_thread.start()

            except Exception as e:
                if self.running:
                    print(f"Ошибка при принятии подключения: {e}")
    
    def handle_client(self, client_socket, address):
        """Обработка клиента"""
        self.clients.append(client_socket)

        try:
            while self.running:
                """Получаем аудио данные от клиента"""
                try:
                    data = client_socket.recv(4096)
                    if not data:
                        break

                    """Пересылаем данные всем другим клиентам"""
                    self.broadcast(data, client_socket)
                
                except socket.error:
                    break
        
        except Exception as e:
            print(f"Ошибка с клиентом {address}: {e}")
        finally:
            self.remove_client(client_socket, address)
    
    def broadcast(self, data, exclude_socket):
        """Отправка данных всем клиентам кроме отправителя"""
        disconnected_clients = []

        for client in self.clients:
            if client != exclude_socket:
                try:
                    client.send(data)
                except socket.error:
                    disconnected_clients.append(client)
        
        """Удаляем отключившихся клиентов"""
        for client in disconnected_clients:
            self.remove_client(client, "disconnected")
    

    def remove_client(self, client_socket, address):
        """Удаление клиента"""
        if client_socket in self.clients:
            self.clients.remove(client_socket)
            try:
                client_socket.close()
            except:
                pass
            print(f"Клиент отключен: {address}")
            print(f"Активных клиентов: {len(self.clients)}")
    
    def control_thread(self):
        """Управление сервером"""
        try:
            while self.running:
                command = input("Введите 'stop' для остановки сервера: ")
                if command.lower() == 'stop':
                    self.stop_server()
                    break
        except KeyboardInterrupt:
            self.stop_server()
    
    def stop_server(self):
        """Остановка сервера"""
        print("Остановка сервера...")
        self.running = False

        """Закрываем все клиентские соединения"""
        for client in self.clients[:]:
            try:
                client.close()
            except:
                pass
        
        self.clients.clear()

        if hasattr(self, 'server_socket'):
            self.server_socket.close()

        self.audio.terminate()
        print("Сервер остановлен")

if __name__ == "__main__":
    server = VoiceServer()
    server.start_server()