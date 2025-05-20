import asyncio
import os
import socket
from datetime import datetime

async def handle_client(reader, writer):
    """
    Handle a client connection, receiving an image file over TCP.
    """
    try:
        # Read file size (8 bytes, big-endian)
        size_data = await reader.readexactly(8)
        file_size = int.from_bytes(size_data, 'big')
        if file_size <= 0:
            print("Error receiving image: Invalid file size")
            return

        # Generate unique filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = "./received_images"
        os.makedirs(output_dir, exist_ok=True)
        filename = os.path.join(output_dir, f"image_{timestamp}.jpg")
        
        # Receive and write image data
        received = 0
        with open(filename, 'wb') as f:
            while received < file_size:
                chunk = await reader.read(4096)  # Match client's chunk size
                if not chunk:
                    print("Error receiving image: Connection closed prematurely")
                    return
                f.write(chunk)
                received += len(chunk)

        # Verify file size
        if received == file_size:
            print(f"Image received successfully: {filename}")
        else:
            print(f"Error receiving image: Incomplete data, received {received}/{file_size} bytes")
        
    except (socket.error, asyncio.IncompleteReadError) as e:
        print(f"Network error receiving image: {e}")
    except Exception as e:
        print(f"Error receiving image: {e}")
    finally:
        writer.close()
        await writer.wait_closed()

async def run_server(host: str = "0.0.0.0", port: int = 5000):
    """
    Run the TCP server to receive images from the Raspberry Pi.
    """
    try:
        server = await asyncio.start_server(handle_client, host, port)
        print(f"Server started on {host}:{port}")
        async with server:
            await server.serve_forever()
    except Exception as e:
        print(f"Server error: {e}")

if __name__ == "__main__":
    # Default settings match send_image's config
    host = "0.0.0.0"  # Listen on all interfaces
    port = 5000
    asyncio.run(run_server(host, port))