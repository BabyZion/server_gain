import datetime
from PyQt5 import QtCore


class Beacon(QtCore.QThread):

    def __init__(self, database, test_devices=None, check_period=None):
        self.time_format = '%Y.%m.%d %H:%M:%S.%f'
        self.db = database
        # self.checkpoint = datetime.datetime.strftime(datetime.datetime.now(), self.time_format)
        self.checkpoint = datetime.datetime.strftime(datetime.datetime.now(), self.time_format)
        self.start_time = datetime.datetime.strftime(datetime.datetime.now(), self.time_format)
        self.test_devices = test_devices
        self.check_period = check_period
        
    def update_test_devices(self):
        # req = f"SELECT DISTINCT imei FROM beacons WHERE timestamp > '{self.start_time}';"
        req = f"SELECT DISTINCT imei FROM beacon_records WHERE timestamp >= '{self.checkpoint}';"
        imeis = self.db.request(req)
        if imeis:
            self.test_devices = []
            for i in imeis:
                if i[0]:
                    self.test_devices.append(i[0])

    def get_device_data(self):
        temp_test_devices = [f"'{i}'" for i in self.test_devices]
        devices = ','.join(temp_test_devices)
        req = f"SELECT imei, uuid, timestamp, signal_str, beacon_records.id FROM beacon_records FULL OUTER JOIN beacons ON beacon_records.id = beacons.record WHERE timestamp >= '{self.checkpoint}';"
        data = self.db.request(req)
        data = sorted(data, key=lambda x:x[4])
        return data

    def calc_stats(self, data):
        results = {}
        for datum in data:
            if datum[0] in self.test_devices or not datum[0]:
                if not results.get(datum[0]):
                    results[datum[0]] = {'all_ts':[]}
                if not results[datum[0]].get(datum[1]):
                    results[datum[0]][datum[1]] = {'timestamps':[], 'signal_str': []}
                results[datum[0]][datum[1]]['timestamps'].append(datum[2])
                results[datum[0]]['all_ts'].append(datum[2])
                if datum[3]:
                    results[datum[0]][datum[1]]['signal_str'].append(datum[3])
        for _, res in results.items():
            all_ts = res['all_ts']
            for _, beac in res.items():

                if type(beac) == dict:
                    beac['missing'] = [ts for ts in all_ts if ts not in beac['timestamps']]
                    beac['visible_pct'] = ((len(all_ts) - len(beac['missing'])) / len(all_ts)) * 100
                    if beac['signal_str']:
                        beac['avg_rssi'] = sum([int(x[:-3]) for x in beac['signal_str']]) / len(beac['signal_str'])
                    else:
                        beac['avg_rssi'] = 0
        return results

    def run(self):
        pass
