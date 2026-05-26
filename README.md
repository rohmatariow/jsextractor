# jsextractor

`jsextractor` is a command-line tool for downloading JavaScript files from a web page.

It extracts JavaScript file URLs from the initial HTML response and downloads them into a local directory. The downloaded files can be used for normal JavaScript review, local inspection, or passed into AI CLI-based tools for JavaScript analysis.

The main script file is:

```text
jsextractor.py
```

After installation, it can be executed globally as:

```bash
jsextractor https://example.com -o example_js
```

## What It Does

`jsextractor` looks for JavaScript files from:

- `<script src="...">`
- `<link rel="preload" as="script" href="...">`
- `<link rel="modulepreload" href="...">`
- `.js` file references inside the HTML source, including inline script payloads

It supports both absolute and relative JavaScript URLs.

## Features

- Download JavaScript files from a web page
- Support relative and absolute JavaScript URLs
- Support modern frontend apps such as Next.js
- Support custom User-Agent
- Support custom HTTP headers
- Support raw Cookie header
- Support cookie file in Netscape/curl cookie jar format
- Automatically creates the output directory
- Adds a short hash to filenames to avoid duplicate filename conflicts
- Shows proper errors when required arguments are missing
- Downloaded files can be used with AI CLI-based JavaScript analysis tools

## Requirements

- Python 3
- `requests`
- `beautifulsoup4`

Install dependencies:

```bash
python3 -m pip install requests beautifulsoup4
```

Or:

```bash
pip3 install requests beautifulsoup4
```

For Kali, Ubuntu, Debian, or systems that block global pip installs:

```bash
sudo apt install -y python3-requests python3-bs4
```

Check Python version:

```bash
python3 --version
```

## Download

Clone this repository:

```bash
git clone https://github.com/rohmatariow/jsextractor.git
cd jsextractor
```

Or download the script directly:

```bash
curl -L -o jsextractor.py https://raw.githubusercontent.com/rohmatariow/jsextractor/main/jsextractor.py
chmod +x jsextractor.py
```


## Run Directly Without Installing

You can run the script directly with Python:

```bash
python3 jsextractor.py https://example.com -o example_js
```

Or make it executable and run it directly:

```bash
chmod +x jsextractor.py
./jsextractor.py https://example.com -o example_js
```

## Installation as Global Command

To run it globally as:

```bash
jsextractor https://example.com -o example_js
```

install `jsextractor.py` into your system path with the command name `jsextractor`.

### macOS Apple Silicon

If you use Homebrew on Apple Silicon, install it to `/opt/homebrew/bin`:

```bash
cp jsextractor.py /opt/homebrew/bin/jsextractor
chmod +x /opt/homebrew/bin/jsextractor
```

Verify:

```bash
which jsextractor
```

Expected output:

```bash
/opt/homebrew/bin/jsextractor
```

Now you can run:

```bash
jsextractor https://example.com -o example_js
```

### macOS Intel or Linux

Install it to `/usr/local/bin`:

```bash
sudo cp jsextractor.py /usr/local/bin/jsextractor
sudo chmod +x /usr/local/bin/jsextractor
```

Verify:

```bash
which jsextractor
```

Expected output:

```bash
/usr/local/bin/jsextractor
```

Now you can run:

```bash
jsextractor https://example.com -o example_js
```

## Usage

Basic usage:

```bash
jsextractor <url> -o <output_dir>
```

Example:

```bash
jsextractor https://example.com -o example_js
```

Run directly with Python:

```bash
python3 jsextractor.py https://example.com -o example_js
```

Run directly as executable:

```bash
./jsextractor.py https://example.com -o example_js
```

Show help:

```bash
jsextractor -h
```

Or:

```bash
python3 jsextractor.py -h
```

## Options

| Option | Description |
|---|---|
| `url` | Target URL. Must start with `http://` or `https://` |
| `-o`, `--output` | Output directory for downloaded JavaScript files |
| `--timeout` | Request timeout in seconds. Default: `20` |
| `-A`, `--user-agent` | Custom User-Agent |
| `-H`, `--header` | Custom HTTP header. Can be used multiple times |
| `-b`, `--cookie` | Raw Cookie header value |
| `--cookie-file` | Cookie file in Netscape/curl cookie jar format |

## Examples

### Basic Download

```bash
jsextractor https://example.com -o example_js
```

### Custom Timeout

```bash
jsextractor https://example.com -o example_js --timeout 30
```

### Custom User-Agent

```bash
jsextractor https://example.com -o example_js -A "Mozilla/5.0"
```

### Custom Header

```bash
jsextractor https://example.com -o example_js \
  -H "Authorization: Bearer TOKEN"
```

### Multiple Custom Headers

```bash
jsextractor https://example.com -o example_js \
  -H "Authorization: Bearer TOKEN" \
  -H "X-Api-Key: API_KEY" \
  -H "X-Custom-Header: value"
```

### Raw Cookie Header

```bash
jsextractor https://example.com -o example_js \
  -b "session=abc123; csrftoken=xyz"
```

### Header and Cookie Together

```bash
jsextractor https://example.com -o example_js \
  -H "Authorization: Bearer TOKEN" \
  -b "session=abc123; csrftoken=xyz"
```

### Cookie File

```bash
jsextractor https://example.com -o example_js \
  --cookie-file cookies.txt
```

The `--cookie-file` option supports Netscape/curl cookie jar format.

Example cookie file line:

```text
.example.com	TRUE	/	FALSE	2147483647	session	abc123
```

## Example Output

```bash
jsextractor https://example.com -o example_js
```

Example output:

```text
[info] found 5 JavaScript files
[info] output: /Users/user/example_js
[ok] https://example.com/static/main.js -> example_js/main.a1b2c3d4.js
[ok] https://example.com/static/vendor.js -> example_js/vendor.e5f6g7h8.js
[done] downloaded 5/5 JavaScript files
```

## Check Downloaded Files

List downloaded JavaScript files:

```bash
find example_js -type f -name "*.js" -print
```

Search inside downloaded JavaScript files:

```bash
grep -Rni "api" example_js
```

## AI CLI-Based Analysis Workflow

After downloading JavaScript files, you can pass the output directory to an AI CLI-based tool or code analysis assistant.

Example:

```bash
jsextractor https://example.com -o example_js
```

Then use `example_js` as the input directory for your AI CLI workflow.

Example analysis prompt:

```text
Analyze the JavaScript files in this directory.

Focus on:
- Application routes
- API references
- Frontend logic
- Hardcoded configuration
- Interesting client-side behavior
- Sensitive strings

Return a structured summary.
```

## Notes

This tool only downloads JavaScript files that are referenced in the initial HTML response.

If a JavaScript file is loaded later by browser execution, dynamic import, lazy loading, route-based loading, or after login, it may not be downloaded by this tool.

For authenticated pages, use `-H`, `-b`, or `--cookie-file` when needed.

## Troubleshooting

### ModuleNotFoundError: No module named bs4

Install `beautifulsoup4`:

```bash
python3 -m pip install beautifulsoup4
```

Or install all dependencies:

```bash
python3 -m pip install requests beautifulsoup4
```

### ModuleNotFoundError: No module named requests

Install `requests`:

```bash
python3 -m pip install requests
```

Or install all dependencies:

```bash
python3 -m pip install requests beautifulsoup4
```

### Command Not Found

If you see:

```bash
zsh: command not found: jsextractor
```

Check your `$PATH`:

```bash
echo $PATH
```

For macOS Apple Silicon, make sure `/opt/homebrew/bin` is in your `$PATH`.

Add it to `~/.zshrc` if needed:

```bash
export PATH="/opt/homebrew/bin:$PATH"
```

Reload your shell:

```bash
source ~/.zshrc
```

### Permission Denied

If you see:

```bash
permission denied: jsextractor
```

Run:

```bash
chmod +x /opt/homebrew/bin/jsextractor
```

Or if installed in `/usr/local/bin`:

```bash
sudo chmod +x /usr/local/bin/jsextractor
```

### Invalid URL

If you see an invalid URL error, make sure the URL starts with `http://` or `https://`.

Correct:

```bash
jsextractor https://example.com -o example_js
```

Incorrect:

```bash
jsextractor example.com -o example_js
```

### Invalid Header Format

If you see an invalid header format error, make sure the header uses this format:

```bash
-H "Header-Name: value"
```
