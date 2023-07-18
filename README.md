# Server Pinger

This project contains a python program which periodically pings a server, logs the response times and can also visualize this data in real-time.

It is a useful tool for network administrators and enthusiasts who want to continuously monitor a server's network performance and understand any network latency or disruption issues. The results can be stored in a CSV file, enabling long-term data analysis.

## Table of Contents

- [Server Pinger](#server-pinger)
  - [Table of Contents](#table-of-contents)
  - [Requirements](#requirements)
  - [Installation](#installation)
  - [Usage](#usage)
  - [Contributing](#contributing)
  - [License](#license)

## Requirements

This project uses the following Python packages:

- argparse
- csv
- time
- ping3
- PySide6
- matplotlib
- socket
- datetime
- signal

Python version 3.7 or above is required. The project may not work as expected with older versions.

## Installation

Before running the script, make sure to install all the required dependencies. It is recommended to create a new virtual environment for this. Here is an example using venv:

```bash
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt
```
The `requirements.txt` file should contain all the necessary packages. As of my current knowledge cutoff in September 2021, I don't have the specific versions used in this project. You may want to ask the project author for the specific package versions.

## Usage

```bash
python main.py [server] [--recall] [-n] [--csv] [--headless]
```
where:
- `server`: The server to ping.
- `--recall`: If used, previously recorded results will be recalled from the specified CSV file.
- `-n`: The interval between pings in seconds. Default is 30 seconds.
- `--csv`: The CSV file to write results to.
- `--headless`: If used, the program will run without a GUI.

If you don't specify a server, the program won't start the ping process.

For example, to ping google.com every 5 seconds and store the result in a file named `ping_result.csv`, you can run:
```bash
python main.py google.com -n 5 --csv ping_result.csv
```

## Contributing

Contributions are welcome! Please open an issue if you find a bug or a pull request for bug fixes, features or improvements.

## License

This project is licensed under the GNU General Public License v3.0 or later. See the `LICENSE` file for details.
