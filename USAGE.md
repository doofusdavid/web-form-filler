# Web Form Filler Usage Guide

This guide provides instructions on how to use the Web Form Filler application to automatically fill out web forms using AI-generated data while rotating IP addresses.

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/web-form-filler.git
   cd web-form-filler
   ```

2. Create a virtual environment and install the package:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -e .
   ```

3. Ensure Ollama is installed and running locally. You can download it from [https://ollama.ai/](https://ollama.ai/).

## Basic Usage

The application can be used as a command-line tool:

```bash
web-form-filler --url "https://example.com/form" --model "llama2" --count 5
```

This will:
1. Analyze the form at the specified URL
2. Generate data for each field using the specified Ollama model
3. Submit the form 5 times with different data each time

## Using IP Rotation

### SOCKS Proxy

To use a SOCKS proxy for IP rotation:

```bash
web-form-filler --url "https://example.com/form" --model "llama2" --count 5 \
  --ip-rotation socks --socks-host "127.0.0.1" --socks-port 1080 \
  --socks-username "your_username" --socks-password "your_password"
```

### PIA VPN

To use PIA VPN for IP rotation:

```bash
web-form-filler --url "https://example.com/form" --model "llama2" --count 5 \
  --ip-rotation pia --pia-username "your_username" --pia-password "your_password"
```

Note: The PIA VPN client must be installed on your system for this to work.

## Example Scripts

The `examples` directory contains several example scripts that demonstrate how to use the application:

### Simple Form Fill

```bash
python examples/simple_form_fill.py
```

This example demonstrates basic form filling without IP rotation.

### SOCKS Proxy Example

```bash
python examples/socks_proxy_example.py --url "https://example.com/form" --model "llama2" \
  --proxy-host "127.0.0.1" --proxy-port 1080
```

This example demonstrates form filling with SOCKS proxy IP rotation.

### PIA VPN Example

```bash
python examples/pia_vpn_example.py --url "https://example.com/form" --model "llama2" \
  --pia-username "your_username" --pia-password "your_password" \
  --servers "us_east,us_west,uk_london"
```

This example demonstrates form filling with PIA VPN IP rotation.

## Advanced Usage

### Customizing Data Generation

The application uses Ollama to generate contextually appropriate data for each form field. You can customize the data generation by modifying the prompts in `web_form_filler/data_generator.py`.

### Honeypot Detection

The application automatically detects potential honeypot fields and leaves them empty. You can customize the honeypot detection logic in `web_form_filler/form_analyzer.py`.

### Logging

The application logs all activity to both the console and a log file in the `logs` directory. You can customize the logging behavior in `web_form_filler/utils/logger.py`.

## Troubleshooting

### Ollama Connection Issues

If you encounter issues connecting to Ollama, ensure that:
1. Ollama is installed and running
2. The Ollama API is accessible at http://localhost:11434
3. The specified model is available in Ollama

### IP Rotation Issues

#### SOCKS Proxy

If you encounter issues with SOCKS proxy IP rotation, ensure that:
1. The SOCKS proxy is running and accessible
2. The proxy host, port, username, and password are correct
3. The proxy supports SOCKS5

#### PIA VPN

If you encounter issues with PIA VPN IP rotation, ensure that:
1. The PIA VPN client is installed and configured
2. The PIA VPN client is accessible via the command line (`piactl`)
3. The PIA username and password are correct
4. The specified server regions are valid

## Legal and Ethical Considerations

Please use this tool responsibly and ethically. Automated form submission may violate the terms of service of some websites, and IP rotation may be used to circumvent rate limits or other restrictions.

Always ensure that your use of this tool complies with applicable laws and regulations, and respect the terms of service of the websites you interact with.