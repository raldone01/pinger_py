import argparse
import csv
import time
from ping3 import ping, verbose_ping
from matplotlib import pyplot as plt
import threading

class Pinger:
    def __init__(self, server, interval=30, csv_file=None, headless=False, recall=False):
        self.server = server
        self.interval = interval
        self.csv_file = csv_file
        self.headless = headless
        self.recall = recall
        self.ping_results = []
        self.running = False
        self.plot_thread = None

        if not self.headless:
            plt.ion()

    def start(self):
        if self.recall:
            self.recall_results()
            return
        self.running = True
        if not self.headless:
            self.plot_thread = threading.Thread(target=self.update_plot)
            self.plot_thread.start()
        self.ping_loop()

    def recall_results(self):
        with open(self.csv_file, 'r', newline='') as f:
            reader = csv.reader(f, delimiter=';')
            for row in reader:
                self.ping_results.append(tuple(row))

        self.update_plot()
        plt.show()

    def ping_loop(self):
        while self.running:
            timestamp = int(time.time())
            try:
                response_time = ping(self.server)
                success = 1 if response_time else 0
            except Exception:
                response_time = None
                success = 0

            response_time_ms = None if response_time is None else round(response_time * 1000)
            result = (timestamp, success, response_time_ms)

            print(f"{timestamp};{success};{response_time_ms}")
            self.ping_results.append(result)

            if self.csv_file:
                with open(self.csv_file, 'a', newline='') as f:
                    writer = csv.writer(f, delimiter=';')
                    writer.writerow(result)

            time.sleep(self.interval)

    def update_plot(self):
        plt.clf()
        plt.ylabel('Response Time (ms)')
        plt.xlabel('Time')
        timestamps, _, response_times = zip(*self.ping_results)
        plt.plot(timestamps, response_times)
        plt.draw()
        plt.pause(1)

    def stop(self):
        self.running = False
        if self.plot_thread:
            self.plot_thread.join()

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
        pinger.stop()

if __name__ == "__main__":
    main()
