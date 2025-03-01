# Web Form Filler

A command-line Python application that automatically fills out web forms using AI-generated data while rotating IP addresses.

## Features

- Analyzes web forms to identify all fields
- Detects potential honeypot fields
- Uses Ollama to generate contextually appropriate data for each field
- Submits forms with the generated data
- Supports IP rotation via SOCKS proxy or PIA VPN
- Repeats the process multiple times with different data

## Requirements

- Python 3.8+
- Ollama (running locally)
- PIA VPN client (optional, for VPN-based IP rotation)

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/web-form-filler.git
cd web-form-filler

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install the package
pip install -e .
```

## Usage

```bash
# Basic usage
web-form-filler --url "https://example.com/form" --model "llama2" --count 5

# With SOCKS proxy for IP rotation
web-form-filler --url "https://example.com/form" --model "llama2" --count 5 \
  --ip-rotation socks --socks-host "127.0.0.1" --socks-port 1080

# With PIA VPN for IP rotation
web-form-filler --url "https://example.com/form" --model "llama2" --count 5 \
  --ip-rotation pia --pia-username "your_username" --pia-password "your_password"

# For more options
web-form-filler --help
```

## Command-Line Options

- `--url`: URL of the web form to fill out (required)
- `--model`: Ollama model to use for generating data (required)
- `--count`: Number of times to fill out the form (default: 1)
- `--ip-rotation`: IP rotation method (none, socks, pia) (default: none)
- `--socks-host`: SOCKS proxy host
- `--socks-port`: SOCKS proxy port
- `--socks-username`: SOCKS proxy username
- `--socks-password`: SOCKS proxy password
- `--pia-username`: PIA VPN username
- `--pia-password`: PIA VPN password
- `--verbose`: Enable verbose output

## License

MIT