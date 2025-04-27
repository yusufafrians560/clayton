from datetime import datetime
import time
from colorama import Fore
import requests
import random
from fake_useragent import UserAgent
import asyncio
import json
import gzip
import brotli
import zlib
import chardet
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import threading


class clayton:
    BASE_URL = "https://tonclayton.fun/api/"
    HEADERS = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "en-GB,en;q=0.9,en-US;q=0.8",
        "referer": "https://tonclayton.fun/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36 Edg/135.0.0.0",
    }

    def __init__(self):
        self.config = self.load_config()
        self.query_list = self.load_query("query.txt")
        self.token = None
        self.session = self.sessions()
        self._original_requests = {
            "get": requests.get,
            "post": requests.post,
            "put": requests.put,
            "delete": requests.delete,
        }
        self.proxy_session = None

    def banner(self) -> None:
        """Displays the banner for the bot."""
        self.log("🎉 Clayton Bot", Fore.CYAN)
        self.log("🚀 Created by LIVEXORDS", Fore.CYAN)
        self.log("📢 Channel: t.me/livexordsscript\n", Fore.CYAN)

    def log(self, message, color=Fore.RESET):
        safe_message = message.encode("utf-8", "backslashreplace").decode("utf-8")
        print(
            Fore.LIGHTBLACK_EX
            + datetime.now().strftime("[%Y:%m:%d ~ %H:%M:%S] |")
            + " "
            + color
            + safe_message
            + Fore.RESET
        )

    def sessions(self):
        session = requests.Session()
        retries = Retry(
            total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504, 520]
        )
        session.mount("https://", HTTPAdapter(max_retries=retries))
        return session

    def decode_response(self, response):
        """
        Mendekode response dari server secara umum.

        Parameter:
            response: objek requests.Response

        Mengembalikan:
            - Jika Content-Type mengandung 'application/json', maka mengembalikan objek Python (dict atau list) hasil parsing JSON.
            - Jika bukan JSON, maka mengembalikan string hasil decode.
        """
        # Ambil header
        content_encoding = response.headers.get("Content-Encoding", "").lower()
        content_type = response.headers.get("Content-Type", "").lower()

        # Tentukan charset dari Content-Type, default ke utf-8
        charset = "utf-8"
        if "charset=" in content_type:
            charset = content_type.split("charset=")[-1].split(";")[0].strip()

        # Ambil data mentah
        data = response.content

        # Dekompresi jika perlu
        try:
            if content_encoding == "gzip":
                data = gzip.decompress(data)
            elif content_encoding in ["br", "brotli"]:
                data = brotli.decompress(data)
            elif content_encoding in ["deflate", "zlib"]:
                data = zlib.decompress(data)
        except Exception:
            # Jika dekompresi gagal, lanjutkan dengan data asli
            pass

        # Coba decode menggunakan charset yang didapat
        try:
            text = data.decode(charset)
        except Exception:
            # Fallback: deteksi encoding dengan chardet
            detection = chardet.detect(data)
            detected_encoding = detection.get("encoding", "utf-8")
            text = data.decode(detected_encoding, errors="replace")

        # Jika konten berupa JSON, kembalikan hasil parsing JSON
        if "application/json" in content_type:
            try:
                return json.loads(text)
            except Exception:
                # Jika parsing JSON gagal, kembalikan string hasil decode
                return text
        else:
            return text

    def load_config(self) -> dict:
        """
        Loads configuration from config.json.

        Returns:
            dict: Configuration data or an empty dictionary if an error occurs.
        """
        try:
            with open("config.json", "r") as config_file:
                config = json.load(config_file)
                self.log("✅ Configuration loaded successfully.", Fore.GREEN)
                return config
        except FileNotFoundError:
            self.log("❌ File not found: config.json", Fore.RED)
            return {}
        except json.JSONDecodeError:
            self.log(
                "❌ Failed to parse config.json. Please check the file format.",
                Fore.RED,
            )
            return {}

    def load_query(self, path_file: str = "query.txt") -> list:
        """
        Loads a list of queries from the specified file.

        Args:
            path_file (str): The path to the query file. Defaults to "query.txt".

        Returns:
            list: A list of queries or an empty list if an error occurs.
        """
        self.banner()

        try:
            with open(path_file, "r") as file:
                queries = [line.strip() for line in file if line.strip()]

            if not queries:
                self.log(f"⚠️ Warning: {path_file} is empty.", Fore.YELLOW)

            self.log(f"✅ Loaded {len(queries)} queries from {path_file}.", Fore.GREEN)
            return queries

        except FileNotFoundError:
            self.log(f"❌ File not found: {path_file}", Fore.RED)
            return []
        except Exception as e:
            self.log(f"❌ Unexpected error loading queries: {e}", Fore.RED)
            return []

    def login(self, index: int) -> None:
        try:
            # Validate index and extract raw token
            if index < 0 or index >= len(self.query_list):
                self.log("❌ Invalid login index. Please check again.", Fore.RED)
                return
            raw_token = self.query_list[index]
            self.log(f"🔐 Using init-data token: {raw_token[:10]}... (truncated)", Fore.CYAN)

            # API 1: GET /user/authorization with init-data header
            auth_url = f"{self.BASE_URL}user/authorization"
            init_data = f"tma {raw_token}"
            auth_headers = {**self.HEADERS, "init-data": init_data}
            try:
                self.log("📡 Requesting authorization...", Fore.CYAN)
                resp = requests.get(auth_url, headers=auth_headers)
                resp.raise_for_status()
                # Login successful, save raw_token as self.token
                self.token = raw_token
                self.log("✅ Login successful. Token saved.", Fore.GREEN)
            except requests.exceptions.RequestException as e:
                self.log(f"❌ Authorization request failed: {e}", Fore.RED)
                return

            # API 2: GET /user/data with init-data header using self.token
            data_url = f"{self.BASE_URL}user/data"
            data_headers = {**self.HEADERS, "init-data": f"tma {self.token}"}
            try:
                self.log("📡 Fetching user data...", Fore.CYAN)
                resp = requests.get(data_url, headers=data_headers)
                resp.raise_for_status()
                data = resp.json()
            except requests.exceptions.RequestException as e:
                self.log(f"❌ Data request failed: {e}", Fore.RED)
                return

            # Display key information
            dr = data.get("daily_reward", {})
            ei = data.get("energy_info", {})
            stats = data.get("stats", {})
            user = data.get("user", {})

            self.log("📅 Daily Reward:", Fore.GREEN)
            self.log(f"    - Current Day: {dr.get('current_day')}", Fore.CYAN)
            self.log(f"    - Can Claim: {dr.get('can_claim')}", Fore.CYAN)

            self.log("⚡ Energy Info:", Fore.GREEN)
            self.log(f"    - Current Energy: {ei.get('current_energy')}/{ei.get('max_energy')}", Fore.CYAN)
            self.log(f"    - Next in: {ei.get('minutes_until_next')}m {ei.get('seconds_until_next')}s", Fore.CYAN)

            self.log("🎮 Stats:", Fore.GREEN)
            self.log(f"    - Games Played: {stats.get('gamesPlayed')}", Fore.CYAN)

            self.log("👤 User:", Fore.GREEN)
            self.log(f"    - Username: {user.get('username')}", Fore.CYAN)
            self.log(f"    - Level: {user.get('level')}", Fore.CYAN)
        except Exception as e:
            self.log(f"❌ Unexpected error in login method: {e}", Fore.RED)

    def daily(self) -> None:
        # Ensure that user is logged in
        if not getattr(self, 'token', None):
            self.log("❌ Cannot fetch daily reward: no token found. Please login first.", Fore.RED)
            return

        # 1) Fetch the latest user data
        try:
            self.log("📡 Fetching daily reward data...", Fore.CYAN)
            data_url = f"{self.BASE_URL}user/data"
            headers = {**self.HEADERS, "init-data": f"tma {self.token}"}
            resp = requests.get(data_url, headers=headers)
            resp.raise_for_status()
            data = resp.json()
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Failed to fetch daily data: {e}", Fore.RED)
            return
        except Exception as e:
            self.log(f"❌ Unexpected error while fetching daily data: {e}", Fore.RED)
            return

        # 2) Extract daily‐reward info
        dr = data.get("daily_reward", {})
        current_day = dr.get("current_day")
        can_claim = dr.get("can_claim", False)
        monthly = dr.get("monthly_rewards", [])

        # 3) Check if claiming is allowed
        if not can_claim:
            self.log(f"⚠️ Cannot claim reward for day {current_day}: can_claim is False.", Fore.YELLOW)
            return

        # 4) Find today's reward slot
        today_reward = next((r for r in monthly if r.get("day") == current_day), None)
        if not today_reward:
            self.log(f"❌ No reward information available for day {current_day}.", Fore.RED)
            return
        if today_reward.get("is_claimed"):
            self.log(f"⚠️ Reward for day {current_day} has already been claimed.", Fore.YELLOW)
            return

        # 5) Claim today's reward
        try:
            self.log(f"📡 Claiming reward for day {current_day}...", Fore.CYAN)
            claim_url = f"{self.BASE_URL}user/daily-claim"
            resp = requests.get(claim_url, headers=headers)
            resp.raise_for_status()
            result = resp.json()
            self.log(f"✅ Claim successful: {result}", Fore.GREEN)
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Daily claim request failed: {e}", Fore.RED)
        except Exception as e:
            self.log(f"❌ Unexpected error in daily method: {e}", Fore.RED)

    def game(self) -> None:
        if not getattr(self, 'token', None):
            self.log("❌ Cannot start game: no token found. Please login first.", Fore.RED)
            return

        headers = {**self.HEADERS, "init-data": f"tma {self.token}"}
        start_url = f"{self.BASE_URL}stack/st-game"
        update_url = f"{self.BASE_URL}stack/update-game"
        end_url = f"{self.BASE_URL}stack/en-game"

        # Fetch initial energy info
        try:
            self.log("📡 Fetching energy info...", Fore.CYAN)
            data_url = f"{self.BASE_URL}user/data"
            resp = requests.get(data_url, headers=headers)
            resp.raise_for_status()
            energy = resp.json().get("energy_info", {}).get("current_energy", 0)
            self.log(f"⚡ Current energy: {energy}", Fore.CYAN)
        except Exception as e:
            self.log(f"❌ Failed to fetch energy info: {e}", Fore.RED)
            return

        if energy <= 0:
            self.log("⚠️ Insufficient energy. Cannot start game.", Fore.YELLOW)
            return

        # Loop main game selama energy masih ada
        while energy > 0:
            try:
                # 1. Start Game
                self.log("🎮 Starting a new game...", Fore.CYAN)
                resp = requests.get(start_url, headers=headers)
                resp.raise_for_status()
                self.log("✅ Game started successfully.", Fore.GREEN)
            except Exception as e:
                self.log(f"❌ Failed to start game: {e}", Fore.RED)
                return

            # 2. Update score bertahap
            total_score = 0
            while True:
                total_score += 10
                payload = {"score": total_score}
                self.log(f"📡 Updating score: {total_score}", Fore.CYAN)
                try:
                    resp = requests.post(update_url, headers=headers, json=payload)
                    if resp.status_code == 500:
                        self.log(f"⚠️ Received 500 on update. Ending game.", Fore.YELLOW)
                        break
                    resp.raise_for_status()
                except Exception as e:
                    self.log(f"❌ Error updating score: {e}. Ending game.", Fore.RED)
                    break
                time.sleep(1)

            # 3. End game
            try:
                self.log("📡 Ending game session...", Fore.CYAN)
                end_payload = {"score": total_score, "multiplier": 1}
                resp = requests.post(end_url, headers=headers, json=end_payload)
                if resp.status_code == 500:
                    self.log(f"⚠️ Server error on end (500). Game ended.", Fore.YELLOW)
                else:
                    resp.raise_for_status()
                    result = resp.json()
                    self.log(f"✅ Game ended. Results: {result}", Fore.GREEN)
            except Exception as e:
                self.log(f"❌ Error ending game session: {e}", Fore.RED)

            # 4. Cek energy lagi setelah end
            try:
                self.log("📡 Refreshing energy info...", Fore.CYAN)
                resp = requests.get(data_url, headers=headers)
                resp.raise_for_status()
                energy = resp.json().get("energy_info", {}).get("current_energy", 0)
                self.log(f"⚡ Current energy after game: {energy}", Fore.CYAN)
            except Exception as e:
                self.log(f"❌ Failed to refresh energy info: {e}", Fore.RED)
                break

        self.log("🏁 No more energy. Finished all games.", Fore.MAGENTA)

    def load_proxies(self, filename="proxy.txt"):
        """
        Reads proxies from a file and returns them as a list.

        Args:
            filename (str): The path to the proxy file.

        Returns:
            list: A list of proxy addresses.
        """
        try:
            with open(filename, "r", encoding="utf-8") as file:
                proxies = [line.strip() for line in file if line.strip()]
            if not proxies:
                raise ValueError("Proxy file is empty.")
            return proxies
        except Exception as e:
            self.log(f"❌ Failed to load proxies: {e}", Fore.RED)
            return []

    def set_proxy_session(self, proxies: list) -> requests.Session:
        """
        Creates a requests session with a working proxy from the given list.

        If a chosen proxy fails the connectivity test, it will try another proxy
        until a working one is found. If no proxies work or the list is empty, it
        will return a session with a direct connection.

        Args:
            proxies (list): A list of proxy addresses (e.g., "http://proxy_address:port").

        Returns:
            requests.Session: A session object configured with a working proxy,
                            or a direct connection if none are available.
        """
        # If no proxies are provided, use a direct connection.
        if not proxies:
            self.log("⚠️ No proxies available. Using direct connection.", Fore.YELLOW)
            self.proxy_session = requests.Session()
            return self.proxy_session

        # Copy the list so that we can modify it without affecting the original.
        available_proxies = proxies.copy()

        while available_proxies:
            proxy_url = random.choice(available_proxies)
            self.proxy_session = requests.Session()
            self.proxy_session.proxies = {"http": proxy_url, "https": proxy_url}

            try:
                test_url = "https://httpbin.org/ip"
                response = self.proxy_session.get(test_url, timeout=5)
                response.raise_for_status()
                origin_ip = response.json().get("origin", "Unknown IP")
                self.log(
                    f"✅ Using Proxy: {proxy_url} | Your IP: {origin_ip}", Fore.GREEN
                )
                return self.proxy_session
            except requests.RequestException as e:
                self.log(f"❌ Proxy failed: {proxy_url} | Error: {e}", Fore.RED)
                # Remove the failed proxy and try again.
                available_proxies.remove(proxy_url)

        # If none of the proxies worked, use a direct connection.
        self.log("⚠️ All proxies failed. Using direct connection.", Fore.YELLOW)
        self.proxy_session = requests.Session()
        return self.proxy_session

    def override_requests(self):
        import random

        """Override requests functions globally when proxy is enabled."""
        if self.config.get("proxy", False):
            self.log("[CONFIG] 🛡️ Proxy: ✅ Enabled", Fore.YELLOW)
            proxies = self.load_proxies()
            self.set_proxy_session(proxies)

            # Override request methods
            requests.get = self.proxy_session.get
            requests.post = self.proxy_session.post
            requests.put = self.proxy_session.put
            requests.delete = self.proxy_session.delete
        else:
            self.log("[CONFIG] proxy: ❌ Disabled", Fore.RED)
            # Restore original functions if proxy is disabled
            requests.get = self._original_requests["get"]
            requests.post = self._original_requests["post"]
            requests.put = self._original_requests["put"]
            requests.delete = self._original_requests["delete"]


async def process_account(account, original_index, account_label, clay, config):

    ua = UserAgent()
    clay.HEADERS["user-agent"] = ua.random

    # Menampilkan informasi akun
    display_account = account[:10] + "..." if len(account) > 10 else account
    clay.log(f"👤 Processing {account_label}: {display_account}", Fore.YELLOW)

    # Override proxy jika diaktifkan
    if config.get("proxy", False):
        clay.override_requests()
    else:
        clay.log("[CONFIG] Proxy: ❌ Disabled", Fore.RED)

    # Login (fungsi blocking, dijalankan di thread terpisah) dengan menggunakan index asli (integer)
    await asyncio.to_thread(clay.login, original_index)

    clay.log("🛠️ Starting task execution...", Fore.CYAN)
    tasks_config = {
        "daily": "Daily Reward Check & Claim 🎁",
        "game": "Play exciting game and earn points 🎮",
    }

    for task_key, task_name in tasks_config.items():
        task_status = config.get(task_key, False)
        color = Fore.YELLOW if task_status else Fore.RED
        clay.log(
            f"[CONFIG] {task_name}: {'✅ Enabled' if task_status else '❌ Disabled'}",
            color,
        )
        if task_status:
            clay.log(f"🔄 Executing {task_name}...", Fore.CYAN)
            await asyncio.to_thread(getattr(clay, task_key))

    delay_switch = config.get("delay_account_switch", 10)
    clay.log(
        f"➡️ Finished processing {account_label}. Waiting {Fore.WHITE}{delay_switch}{Fore.CYAN} seconds before next account.",
        Fore.CYAN,
    )
    await asyncio.sleep(delay_switch)


async def worker(worker_id, clay, config, queue):
    """
    Setiap worker akan mengambil satu akun dari antrian dan memprosesnya secara berurutan.
    Worker tidak akan mengambil akun baru sebelum akun sebelumnya selesai diproses.
    """
    while True:
        try:
            original_index, account = queue.get_nowait()
        except asyncio.QueueEmpty:
            break
        account_label = f"Worker-{worker_id} Account-{original_index+1}"
        await process_account(account, original_index, account_label, clay, config)
        queue.task_done()
    clay.log(f"Worker-{worker_id} finished processing all assigned accounts.", Fore.CYAN)


async def main():
    clay = clayton()  
    config = clay.load_config()
    all_accounts = clay.query_list
    num_threads = config.get("thread", 1)  # Jumlah worker sesuai konfigurasi

    if config.get("proxy", False):
        proxies = clay.load_proxies()

    clay.log(
        "🎉 [LIVEXORDS] === Welcome to Clayton Automation === [LIVEXORDS]", Fore.YELLOW
    )
    clay.log(f"📂 Loaded {len(all_accounts)} accounts from query list.", Fore.YELLOW)

    while True:
        # Buat queue baru dan masukkan semua akun (dengan index asli)
        queue = asyncio.Queue()
        for idx, account in enumerate(all_accounts):
            queue.put_nowait((idx, account))

        # Buat task worker sesuai dengan jumlah thread yang diinginkan
        workers = [
            asyncio.create_task(worker(i + 1, clay, config, queue))
            for i in range(num_threads)
        ]

        # Tunggu hingga semua akun di queue telah diproses
        await queue.join()

        # Opsional: batalkan task worker (agar tidak terjadi tumpang tindih)
        for w in workers:
            w.cancel()

        clay.log("🔁 All accounts processed. Restarting loop.", Fore.CYAN)
        delay_loop = config.get("delay_loop", 30)
        clay.log(
            f"⏳ Sleeping for {Fore.WHITE}{delay_loop}{Fore.CYAN} seconds before restarting.",
            Fore.CYAN,
        )
        await asyncio.sleep(delay_loop)


if __name__ == "__main__":
    asyncio.run(main())
