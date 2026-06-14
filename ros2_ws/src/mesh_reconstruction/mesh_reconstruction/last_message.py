#!/usr/bin/env python3
"""
Extract the last message of a topic from a ROS2 bag and write it to a new bag.

Usage:
    python3 extract_last_message.py <input_bag_dir> <output_bag_dir> [topic_name]

If topic_name is omitted and the bag has only one topic, that topic is used
automatically.

Note: <input_bag_dir> and <output_bag_dir> are bag DIRECTORIES (the folder
containing metadata.yaml + the .mcap file), not the .mcap file itself.
<output_bag_dir> must not already exist.
"""

import sys
import rosbag2_py


def extract_last_message(input_bag, output_bag, topic_name=None):
    storage_options_in = rosbag2_py.StorageOptions(uri=input_bag, storage_id='mcap')
    converter_options = rosbag2_py.ConverterOptions(
        input_serialization_format='cdr',
        output_serialization_format='cdr'
    )

    reader = rosbag2_py.SequentialReader()
    reader.open(storage_options_in, converter_options)

    topics_and_types = reader.get_all_topics_and_types()
    type_map = {t.name: t for t in topics_and_types}

    if topic_name is None:
        if len(type_map) != 1:
            raise ValueError(
                f"Bag has multiple topics ({list(type_map)}); "
                f"specify which one to extract."
            )
        topic_name = next(iter(type_map))

    if topic_name not in type_map:
        raise ValueError(f"Topic '{topic_name}' not found. Available: {list(type_map)}")

    last_data, last_ts = None, None
    count = 0
    while reader.has_next():
        topic, data, ts = reader.read_next()
        if topic == topic_name:
            last_data, last_ts = data, ts
            count += 1

    if last_data is None:
        raise RuntimeError(f"No messages found on topic '{topic_name}'")

    storage_options_out = rosbag2_py.StorageOptions(uri=output_bag, storage_id='mcap')
    writer = rosbag2_py.SequentialWriter()
    writer.open(storage_options_out, converter_options)
    writer.create_topic(type_map[topic_name])
    writer.write(topic_name, last_data, last_ts)

    print(f"Scanned {count} messages on '{topic_name}'")
    print(f"Wrote last message (timestamp {last_ts}) to '{output_bag}'")


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <input_bag_dir> <output_bag_dir> [topic_name]")
        sys.exit(1)

    input_bag = sys.argv[1]
    output_bag = sys.argv[2]
    topic = sys.argv[3] if len(sys.argv) > 3 else None

    extract_last_message(input_bag, output_bag, topic)