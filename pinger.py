import argparse
import csv
import time
from ping3 import ping
from matplotlib import pyplot as plt
from socket import gethostbyname
from datetime import datetime
from matplotlib.dates import DateFormatter, HourLocator, date2num
from matplotlib.ticker import MaxNLocator

class Pinger:
    def __init__(self, server, interval=30, csv_file=None, headless=False, recall=False):
        self.server = server
        self.ip = gethostbyname(self.server) if self.server else None
        self.interval = interval
        self.csv_file = csv_file
        self.headless = headless
        self.recall = recall
        self.ping_results = []

        if not self.headless:
            plt.ion()

    def start(self):
        if self.recall:
            self.recall_results()
            return
        self.ping_loop()

    def recall_results(self):
        with open(self.csv_file, 'r', newline='') as f:
            reader = csv.reader(f, delimiter=';')
            for row in reader:
                timestamp = datetime.fromtimestamp(int(row[0]))
                self.ping_results.append((timestamp,) + tuple(row[1:]))

        self.update_plot()
        plt.show(block=True)

    def ping_loop(self):
        while True:
            timestamp = int(time.time())
            try:
                response_time = ping(self.server)
                success = 1 if response_time else 0
            except Exception:
                response_time = None
                success = 0

            response_time_ms = None if response_time is None else round(response_time * 1000)
            result = (timestamp, self.ip, success, response_time_ms)

            print(f"{timestamp};{self.ip};{success};{response_time_ms}")
            self.ping_results.append((datetime.fromtimestamp(timestamp), self.ip, success, response_time_ms))

            if self.csv_file:
                with open(self.csv_file, 'a', newline='') as f:
                    writer = csv.writer(f, delimiter=';')
                    writer.writerow(result)

            time.sleep(self.interval)

            if not self.headless:
                self.update_plot()

    def update_plot(self):
        plt.clf()
        plt.title(f"Ping Response Time for {self.server} - {self.ip}")
        plt.ylabel('Response Time (Milliseconds)')
        plt.xlabel('Time')
        plt.grid(True)
        timestamps, _, successes, response_times = zip(*self.ping_results)
        for t, s in zip(timestamps, successes):
            if s == 0:
                plt.axvline(x=t, color='r', linewidth=2)
        plt.plot(timestamps, response_times)
        plt.gcf().autofmt_xdate()  # for formatting the x-axis nicely
        plt.gca().xaxis.set_major_locator(MaxNLocator(10))
        plt.gca().xaxis.set_major_formatter(DateFormatter('%H:%M'))
        plt.draw()
        plt.pause(1)

def main():
    parser = argparse.ArgumentParser(description='Ping a server periodically.')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('server', type=str, nargs='?', default=None, help='The server to ping.')
    group.add_argument('--recall', action='store_true', help='Recall recorded results.')
    parser.add_argument('-n', type=int, default=30, help='The interval between pings.')
    parser.add_argument('--csv', type=str, help='The CSV file to write results to.')
    parser.add_argument('--headless', action='store_true', help='Do not display a plot.')
    args = parser.parse_args()

    pinger = Pinger(args.server, args.n, args.csv, args.headless, args.recall)
    try:
        pinger.start()
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
