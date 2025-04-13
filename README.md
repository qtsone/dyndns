# Dynamic DNS Updater

A Kubernetes-ready dynamic DNS updater with plugin support. Currently supports Cloudflare DNS provider.

## Features

- Plugin-based architecture for easy extension
- Cloudflare DNS provider support
- Kubernetes-ready with proper security context
- Configurable update intervals
- Comprehensive logging
- Secure credential management
- Helm chart for easy deployment

## Prerequisites

- Python 3.11+
- Docker
- Kubernetes cluster
- Cloudflare account and API credentials
- Helm 3+ (for Helm deployment)

## Local Development

1. Clone the repository:
```bash
git clone https://github.com/qtsone/dyndns.git
cd dyndns
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
export CLOUDFLARE_ZONE_ID="your_zone_id"
export CLOUDFLARE_API_KEY="your_api_key"
export DNS_RECORDS="domain1.com,domain2.com,domain3.com"
```

4. Run the updater:
```bash
python -m dyndns
```

## Docker Build

1. Build the Docker image:
```bash
docker build -t dyndns:latest .
```

2. Run the container:
```bash
docker run -d \
  --name dyndns \
  -e CLOUDFLARE_ZONE_ID=your_zone_id \
  -e CLOUDFLARE_API_KEY=your_api_key \
  -e DNS_RECORDS=domain1.com,domain2.com,domain3.com \
  dyndns:latest
```

## Kubernetes Deployment

### Using Helm

1. Navigate to the Helm chart directory:
```bash
cd helm/dyndns
```

2. Create a custom values file (e.g., `my-values.yaml`):
```yaml
config:
  cloudflareZoneId: "your-zone-id"
  dnsRecord: "your-domain.com"
  proxied: "true"
  provider: "cloudflare"
  logLevel: "INFO"
secret:
  cloudflareApiToken: "your-base64-encoded-token"
```

3. Install the chart:
```bash
helm install dyndns . -f my-values.yaml
```

4. To upgrade your release:
```bash
helm upgrade dyndns . -f my-values.yaml
```

5. To uninstall/delete the deployment:
```bash
helm uninstall dyndns
```

## Configuration

### Environment Variables

- `CLOUDFLARE_ZONE_ID`: Your Cloudflare zone ID
- `CLOUDFLARE_API_KEY`: Your Cloudflare API key
- `DNS_RECORDS`: Comma-separated list of DNS records to update
- `INTERVAL`: Update interval in seconds (default: 300)
- `LOG_LEVEL`: Logging level (default: INFO)
- `PROXIED`: Whether to proxy the record through Cloudflare (default: true)

## Adding New Providers

To add a new DNS provider:

1. Create a new class that inherits from `DNSProvider`
2. Implement the required methods:
   - `get_current_ip()`
   - `get_dns_record()`
   - `update_dns_record()`
3. Add the provider to the `get_provider()` function in `__main__.py`

## License

This project is licensed under the GPL License - see the [LICENSE](LICENSE) file for details.
