# Nutri Stacker

Nutri Stacker is a Streamlit app for building meals and reviewing macro- and micronutrient intake.

The application:

- loads food data from `food.json`
- calculates meal macros and micronutrients
- lets users define and save nutrition targets
- saves and reloads meals as JSON files
- provides an installable PWA shell for Android and desktop browsers

## Run the Streamlit app

Install the Python dependencies and start Streamlit:

```bash
pip install -r requirements.txt
streamlit run main.py
```

The Streamlit app is available at `http://localhost:8501/streamlit/` by default.

## Production architecture

The PWA shell and Streamlit app are separate HTTP services:

```text
https://nutri-meal-app.example/
    -> PWA shell service on port 5500

https://nutri-meal-app.example/streamlit/
    -> Streamlit service on port 8501
```

Users should access and install the root URL. The shell embeds Streamlit through
the same-origin `/streamlit/` path. The Streamlit port should remain private and
only be reachable by the reverse proxy.

The reverse proxy must:

1. terminate HTTPS
2. route `/` to the PWA shell service
3. route `/streamlit/` to Streamlit
4. forward WebSocket connections for `/streamlit/`
5. avoid caching Streamlit HTML, API, and WebSocket traffic

The repository includes [`.streamlit/config.toml`](.streamlit/config.toml), which
configures the server for both local and production use:

```toml
[server]
address = "0.0.0.0"
port = 8501
headless = true
baseUrlPath = "streamlit"
```

The `baseUrlPath` setting makes Streamlit available below `/streamlit/`, matching
the reverse-proxy route and the PWA shell. If your deployment needs to override
the file, the equivalent environment variable is:

```text
STREAMLIT_SERVER_BASE_URL_PATH=streamlit
```

Run the shell service in the second container or process:

```bash
python pwa_server.py --host 0.0.0.0 --port 5500
```

The PWA shell only caches its own static assets. It does not cache nutrition
data, user targets, saved meals, Streamlit responses, or WebSocket traffic.
The app therefore remains server-side and requires a live connection, as
intended.

Streamlit documents [`server.baseUrlPath`](https://docs.streamlit.io/develop/api-reference/configuration/config.toml)
for serving an app below a URL path and recommends using a
[reverse proxy](https://docs.streamlit.io/knowledge-base/deploy/deploy-streamlit-domain-port-80)
when exposing Streamlit through a normal domain.

## Local PWA testing

For local development, start both services in separate terminals:

Terminal 1:

```bash
streamlit run main.py
```

Terminal 2:

```bash
python pwa_server.py --host 0.0.0.0 --port 5500
```

Open the shell from another device on the same network:

```text
http://<computer-ip>:5500
```

The local shell automatically embeds Streamlit from
`http://<computer-ip>:8501/streamlit/`.

### Android install testing with ADB

An HTTP LAN address such as `http://192.168.x.x:5500` is not a secure context,
so Chrome Android may display the shell but will not treat it as a fully
installable PWA. To test installation locally over USB, forward both ports to
Android localhost:

```bash
adb reverse tcp:5500 tcp:5500
adb reverse tcp:8501 tcp:8501
```

Then open this URL on Android:

```text
http://localhost:5500
```

For production, use the HTTPS domain handled by the reverse proxy.

## Important files

- `main.py`: Streamlit entry point
- `app/`: application UI, storage, translations, configuration, and calculations
- `food.json`: food and nutrient database
- `user_targets.json`: locally persisted nutrition targets
- `saved_meals/`: locally persisted meal files
- `pwa/index.html`: installable shell that embeds Streamlit
- `pwa/manifest.json`: PWA installation metadata
- `pwa/sw.js`: shell-only service worker
- `pwa/icon.svg`: application icon
- `pwa_server.py`: local or containerized static shell server
