#!/usr/bin/python3

import re
import binascii
import libscrc
from datetime import datetime

TCP_PACKET_PATTERN = re.compile(r'Packet len: .*, data: .*\n.*(this is correct single packet|no 0x31 at the end)')
UDP_PACKET_PATTERN = re.compile(r'Packet len: .*, data: .*\n.*received imei:.*\n.*sending udp')
PACKET_PATTERN = re.compile(r'((Packet len: .*, data: .*\n.*(this is correct single packet|no 0x31 at the end))|(Packet len: .*, data: .*\n.*received imei:.*\n.*sending udp))')
DATE_PATTERN = re.compile(r'\d{4}\.\d{2}\.\d{2}\s\d{2}:\d{2}:\d{2}')

def parse_log(log):
    """
    Parses supplied string object and finds packets containing record information.
    Returns the list of said data packets.

        Parameters:
            log (str): a string representing a log of server_main.

        Returns:
            packets (list of tuples): returns a list with packets containing the string date of when packet
            was received and packet data in string format.
    """
    packet_matches = PACKET_PATTERN.finditer(log)
    packets = []
    for match in packet_matches:
        match_string = match.group()
        packet = match.group().split(':')[2].split('\n')[0].strip()
        time_received = re.search(DATE_PATTERN, match_string).group()
        time_received = datetime.strptime(time_received, '%Y.%m.%d %H:%M:%S')
        packets.append((time_received, packet))
    return packets

def parse_packet(packet):
    """
    Goes through supplied string representation of data packet and parses its parts.
    Considers record as a single part of a packet.

        Parameters:
            packet (tuple): tuple containing the string date of when packet
            was received and packet data in string format.

        Returns:
            packet_info (dict): a dict with various parts of data packet.
    """
    time_received, packet = packet
    if packet[4:8].upper() == 'CAFE':
        packet_info, reply = __parse_udp_packet(packet)
    else:
        packet_info, reply = __parse_tcp_packet(packet)
    packet_info['time_received'] = time_received
    return packet_info, reply

def parse_date(log):
    """
    Parses supplied string object and finds date strings and returns them.

        Parameters:
            log (str): a string representing a log of server_main.

        Returns:
            dates (list): returns a list with string representation of dates found in the log supplied.
            was received and packet data in string format.
    """
    str_dates = DATE_PATTERN.findall(log)
    dates = [datetime.strptime(d, '%Y.%m.%d %H:%M:%S') for d in str_dates]
    return dates

def __parse_tcp_packet(packet):
    """
    Function used in parse packets function. Specificaly parses TCP packets.

        Parameters:
            packet (str): a string representation of data packet.

        Returns:
            packet_info (dict): a dict with various parts of data packet.
    """
    rest_of_packet = packet
    zeros, rest_of_packet = rest_of_packet[:8], rest_of_packet[8:]
    data_length, rest_of_packet = rest_of_packet[:8], rest_of_packet[8:]
    codec, rest_of_packet = rest_of_packet[:2], rest_of_packet[2:]
    no_of_data_1, rest_of_packet = rest_of_packet[:2], rest_of_packet[2:]
    records, rest_of_packet = rest_of_packet[:-10], rest_of_packet[-10:]
    no_of_data_2, rest_of_packet = rest_of_packet[:2], rest_of_packet[2:]
    crc_16 = rest_of_packet
    packet_info = {'protocol':'TCP', 'zeros':zeros, 'data_length':data_length, 'codec':codec,
        'no_of_data_1':no_of_data_1, 'records':records, 'no_of_data_2':no_of_data_2, 'crc_16':crc_16}
    reply = build_record_reply(packet_info['protocol'], no_of_data_1)
    return packet_info, reply
    
def __parse_udp_packet(packet):
    """
    Function used in parse packets function. Specificaly parses UDP packets.

        Parameters:
            packet (str): a string representation of data packet.

        Returns:
            packet_info (dict): a dict with various parts of data packet.
    """
    rest_of_packet = packet
    data_length, rest_of_packet = rest_of_packet[:4], rest_of_packet[4:]
    identification, rest_of_packet = rest_of_packet[:4], rest_of_packet[4:]
    not_used, rest_of_packet = rest_of_packet[:2], rest_of_packet[2:]
    packet_id, rest_of_packet = rest_of_packet[:2], rest_of_packet[2:]
    imei_len, rest_of_packet = rest_of_packet[:4], rest_of_packet[4:]
    imei, rest_of_packet = rest_of_packet[:30], rest_of_packet[30:]
    codec, rest_of_packet = rest_of_packet[:2], rest_of_packet[2:]
    no_of_data_1, rest_of_packet = rest_of_packet[:2], rest_of_packet[2:]
    records, rest_of_packet = rest_of_packet[:-2], rest_of_packet[-2:]
    no_of_data_2 = rest_of_packet
    packet_info = {'protocol':'UDP', 'data_length':data_length, 'identification':identification, 'not_used':not_used,
        'packet_id':packet_id, 'imei_len':imei_len, 'imei':imei, 'codec':codec,
            'no_of_data_1':no_of_data_1, 'records':records, 'no_of_data_2':no_of_data_2}
    reply = build_record_reply(packet_info['protocol'], no_of_data_1, packet_id)
    return packet_info, reply

def parse_record_payload(record_payload, no_of_records, codec='08'):
    """
    Parses packet payload containing records. Puts every parameter into a dict. Each dict represents a single record.
    dicts are appended to the list which is than returned.

        Parameters:
            record_payload (str): a string representation record data.
            no_of_records (int): a number of records in record_payload.
            codec (str): type of codec used to encode records. Default '08'.

        Returns:
            records (list of dicts): a list containing dicts representing records.
            reply (str): str representation of bytes that are sent to device as an ack of received records.
    """
    records = []
    rest_of_payload = record_payload
    mx = 1 if codec == '08' else 2
    no_of_records_hex = no_of_records
    no_of_records = int(no_of_records, 16)
    recs_parsed = 0
    while recs_parsed < no_of_records:
        timestamp, rest_of_payload = rest_of_payload[:16], rest_of_payload[16:]
        priority, rest_of_payload = rest_of_payload[:2], rest_of_payload[2:]
        gps_data, rest_of_payload = rest_of_payload[:30], rest_of_payload[30:]
        event_id, rest_of_payload = rest_of_payload[:2*mx], rest_of_payload[2*mx:]
        no_of_io, rest_of_payload = rest_of_payload[:2*mx], rest_of_payload[2*mx:]
        record = {'timestamp':timestamp, 'priority':priority, 'gps_data':gps_data,
            'event_id':event_id, 'no_of_io':no_of_io}
        for i in range(4):
            value_len = (2 ** i) * 2
            no_of_elements_x_byte, rest_of_payload = rest_of_payload[:2*mx], rest_of_payload[2*mx:]
            no_of_elements_x_byte = int(no_of_elements_x_byte, 16)
            for _ in range(no_of_elements_x_byte):
                avl_id, rest_of_payload = rest_of_payload[:2*mx], rest_of_payload[2*mx:]
                value, rest_of_payload = rest_of_payload[:value_len], rest_of_payload[value_len:]
                record[avl_id] = value
        if codec == '8E':
            no_of_elements_x_byte, rest_of_payload = rest_of_payload[:2*mx], rest_of_payload[2*mx:]
            no_of_elements_x_byte = int(no_of_elements_x_byte, 16)
            for _ in range(no_of_elements_x_byte):
                avl_id, rest_of_payload = rest_of_payload[:2*mx], rest_of_payload[2*mx:]
                value_len, rest_of_payload = rest_of_payload[:2*mx], rest_of_payload[2*mx:]
                value_len = int(value_len, 16) * 2
                value, rest_of_payload = rest_of_payload[:value_len], rest_of_payload[value_len:]
                record[avl_id] = value
        recs_parsed += 1
        records.append(record)
    return records

def parse_imei(data, wlen=True):
    """
    Parses IMEI from data received while establishing connection.

        Parameters:
            data (str): received data from device as a str object.

        Returns:
            imei (str): parsed IMEI in decimal format.
    """
    imei_hex = data[4:] if wlen else data
    imei = binascii.unhexlify(data).decode('utf-8')
    return imei

def build_gprs_cmd(cmd):
    """
    Builds a packet required to send GPRS command to device successfully.

        Parameters:
            cmd (str): GPRS command to send to the device.

        Returns:
            packet (str): str representation of bytes of GPRS command and other fields
            requirerd to send a command.
    """
    cmd = binascii.hexlify(cmd.encode('utf-8')).decode('utf-8')
    four_zeros = '00000000'
    codec = '0C'
    no_of_cmds = '01'
    type_byte = '05' # GPRS cmd to send. 06 would be cmd response received from device.
    cmd_len = hex(int(len(cmd)/2))[2:].zfill(8)
    packet = codec + no_of_cmds + type_byte + cmd_len + cmd + no_of_cmds
    packet_len = hex(int(len(packet) / 2))[2:]
    packet_len = packet_len.zfill(8)
    full_packet = four_zeros + packet_len + packet
    packet_bytes = binascii.unhexlify(packet)
    crc16 = hex(libscrc.ibm(packet_bytes))[2:].zfill(8)
    full_packet += crc16
    return full_packet

def parse_gprs_cmd_response(data):
    """
    Parses GPRS CMD response from data received.

        Parameters:
            data (str): received data from device as a str object.

        Returns:
            response (str): human readable response to GPRS command.
    """
    response = binascii.unhexlify(data[10:]).decode('utf-8')
    return response

def build_record_reply(protocol, no_of_recs, packet_id=None):
    """
    Builds reply of record packet received.

        Parameters:
            protocol (str): transport protocol of received packet.
            no_of_recs (int): number of records in data packet.
            packet_id (str): UDP packet id.
    """
    if protocol == 'TCP':
        return '0' * (8 - len(no_of_recs)) + no_of_recs
    elif protocol == 'UDP':
        return '0' * (14 - len(no_of_recs + packet_id)) + packet_id + no_of_recs