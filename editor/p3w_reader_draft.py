# file_directory =

with open('CGM5-30405-241121 Bottom.p3w', 'rb') as f:
    content = f.read()  # Read the first 200 bytes

print(content)  # Peek at the first 100 bytes

# import struct
#
# def decode_p3w(filepath, output_txt='output.txt'):
#     with open(filepath, 'rb') as f:
#         data = f.read()
#
#     record_size = 20  # 5 float32 values (4 bytes each)
#     num_records = len(data) // record_size
#
#     with open(output_txt, 'w') as out:
#         for i in range(num_records):
#             offset = i * record_size
#             record = data[offset:offset + record_size]
#             if len(record) == 20:
#                 time, depth, tension, weight, pressure = struct.unpack('<5f', record)
#                 out.write(f"{time:.2f}, {depth:.2f}, {tension:.3f}, {weight:.2f}, {pressure:.2f}\n")
#
#     print(f"Decoded {num_records} records to '{output_txt}'.")
#
# # Example usage:
# decode_p3w('CGM5-30405-241121 Bottom.p3w')
