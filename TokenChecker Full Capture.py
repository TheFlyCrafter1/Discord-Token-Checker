import requests
import json
import os
import time
from datetime import datetime

class DiscordTokenChecker:
    def __init__(self):
        self.discord_api = "https://discord.com/api/v9"
        self.results = []
        
    def check_token(self, token, verbose=True):
        """
        Check if a Discord token is valid
        Returns: (is_valid, user_info, error_message)
        """
        headers = {
            "Authorization": token,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        try:
            # Try to get user info
            response = requests.get(
                f"{self.discord_api}/users/@me",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                user_data = response.json()
                
                # Get additional info like guilds
                guilds_response = requests.get(
                    f"{self.discord_api}/users/@me/guilds",
                    headers=headers,
                    timeout=10
                )
                
                guilds = []
                if guilds_response.status_code == 200:
                    guilds = guilds_response.json()
                
                user_info = {
                    "id": user_data.get("id"),
                    "username": user_data.get("username"),
                    "discriminator": user_data.get("discriminator"),
                    "email": user_data.get("email"),
                    "verified": user_data.get("verified", False),
                    "phone": user_data.get("phone"),
                    "mfa_enabled": user_data.get("mfa_enabled", False),
                    "guild_count": len(guilds),
                    "guilds": guilds[:5]  # First 5 guilds
                }
                
                if verbose:
                    print(f"✓ VALID TOKEN")
                    print(f"  User: {user_info['username']}#{user_info['discriminator']}")
                    print(f"  ID: {user_info['id']}")
                    print(f"  Email: {user_info['email'] or 'Not set'}")
                    print(f"  Verified: {user_info['verified']}")
                    print(f"  Phone: {user_info['phone'] or 'Not set'}")
                    print(f"  2FA: {'Enabled' if user_info['mfa_enabled'] else 'Disabled'}")
                    print(f"  Servers: {user_info['guild_count']}")
                
                return True, user_info, None
                
            elif response.status_code == 401:
                if verbose:
                    print("✗ INVALID TOKEN")
                return False, None, "Invalid token"
            elif response.status_code == 403:
                if verbose:
                    print("⚠ TOKEN LOCKED (Password changed or disabled)")
                return False, None, "Token locked"
            else:
                if verbose:
                    print(f"✗ ERROR: HTTP {response.status_code}")
                return False, None, f"HTTP {response.status_code}"
                
        except requests.exceptions.RequestException as e:
            if verbose:
                print(f"✗ CONNECTION ERROR: {str(e)}")
            return False, None, f"Connection error: {str(e)}"
    
    def check_single_token(self):
        """Interactive single token check"""
        print("\n" + "="*50)
        print("SINGLE TOKEN CHECK")
        print("="*50)
        token = input("Enter Discord token: ").strip()
        
        print("\nChecking token...")
        valid, info, error = self.check_token(token)
        
        if valid and info:
            # Save valid token
            self.results.append({
                "token": token,
                "valid": True,
                "info": info,
                "timestamp": datetime.now().isoformat()
            })
            self.save_results()
    
    def bulk_check_from_file(self, filename="tokens.txt", delay=1.0):
        """
        Bulk check tokens from a text file
        Each line should contain one token
        """
        if not os.path.exists(filename):
            print(f"Error: File '{filename}' not found!")
            return
        
        with open(filename, 'r') as file:
            tokens = [line.strip() for line in file if line.strip()]
        
        if not tokens:
            print("No tokens found in the file!")
            return
        
        print(f"\nFound {len(tokens)} token(s) in {filename}")
        print("="*50)
        
        valid_tokens = 0
        invalid_tokens = 0
        locked_tokens = 0
        error_tokens = 0
        
        for idx, token in enumerate(tokens, 1):
            # Mask token for display
            masked_token = token[:20] + "..." + token[-5:] if len(token) > 25 else token
            print(f"\n[{idx}/{len(tokens)}] Checking: {masked_token}")
            
            valid, info, error = self.check_token(token, verbose=True)
            
            if valid:
                valid_tokens += 1
                self.results.append({
                    "token": token,
                    "valid": True,
                    "info": info,
                    "timestamp": datetime.now().isoformat()
                })
            elif error == "Token locked":
                locked_tokens += 1
                self.results.append({
                    "token": token,
                    "valid": False,
                    "error": error,
                    "timestamp": datetime.now().isoformat()
                })
            elif error and "Invalid" in error:
                invalid_tokens += 1
                self.results.append({
                    "token": token,
                    "valid": False,
                    "error": error,
                    "timestamp": datetime.now().isoformat()
                })
            else:
                error_tokens += 1
                self.results.append({
                    "token": token,
                    "valid": False,
                    "error": error,
                    "timestamp": datetime.now().isoformat()
                })
            
            # Delay between requests
            if idx < len(tokens):
                time.sleep(delay)
        
        # Summary
        self.print_summary(valid_tokens, invalid_tokens, locked_tokens, error_tokens)
        self.save_results()
    
    def print_summary(self, valid, invalid, locked, errors):
        """Print check summary"""
        total = valid + invalid + locked + errors
        
        print("\n" + "="*50)
        print("BULK CHECK SUMMARY")
        print("="*50)
        print(f"Total tokens checked: {total}")
        print(f"✓ Valid tokens: {valid}")
        print(f"✗ Invalid tokens: {invalid}")
        print(f"⚠ Locked tokens: {locked}")
        print(f"❌ Error tokens: {errors}")
        
        if valid > 0:
            print(f"\n✅ Valid tokens found: {valid}")
    
    def save_results(self, filename="token_check_results.json"):
        """Save results to JSON file"""
        if not self.results:
            return
        
        with open(filename, 'w') as file:
            json.dump(self.results, file, indent=2, default=str)
        
        print(f"\nResults saved to: {filename}")
        
        # Also save valid tokens to a separate file
        valid_tokens = [r for r in self.results if r.get("valid")]
        if valid_tokens:
            valid_file = "valid_tokens.txt"
            with open(valid_file, 'w') as file:
                for token_data in valid_tokens:
                    file.write(f"{token_data['token']}\n")
            print(f"Valid tokens saved to: {valid_file}")
    
    def load_results(self, filename="token_check_results.json"):
        """Load previous results"""
        if os.path.exists(filename):
            with open(filename, 'r') as file:
                self.results = json.load(file)
            print(f"Loaded {len(self.results)} previous results")
    
    def export_to_csv(self, filename="token_check_results.csv"):
        """Export results to CSV for easy viewing"""
        import csv
        
        with open(filename, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(["Token", "Valid", "Username", "ID", "Email", "Verified", "2FA", "Servers", "Error", "Timestamp"])
            
            for result in self.results:
                token = result["token"]
                valid = result["valid"]
                
                if valid and "info" in result:
                    info = result["info"]
                    writer.writerow([
                        token[:20] + "...",  # Masked token
                        "Yes",
                        f"{info['username']}#{info['discriminator']}",
                        info['id'],
                        info['email'] or "",
                        info['verified'],
                        "Yes" if info['mfa_enabled'] else "No",
                        info['guild_count'],
                        "",
                        result['timestamp']
                    ])
                else:
                    writer.writerow([
                        token[:20] + "...",
                        "No",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        result.get('error', 'Unknown'),
                        result['timestamp']
                    ])
        
        print(f"Results exported to CSV: {filename}")

def main():
    checker = DiscordTokenChecker()
    
    print("="*50)
    print("Discord Token Checker leaked by ntpx")
    while True:
        print("\nOPTIONS:")
        print("1. Check single token")
        print("2. Bulk check from tokens.txt")
        print("3. Bulk check from custom file")
        print("4. View previous results")
        print("5. Export results to CSV")
        print("6. Exit")
        
        choice = input("\nSelect option (1-6): ").strip()
        
        if choice == "1":
            checker.check_single_token()
            
        elif choice == "2":
            delay = input("Enter delay between checks in seconds (default 1.0): ").strip()
            delay = float(delay) if delay else 1.0
            checker.bulk_check_from_file("tokens.txt", delay)
            
        elif choice == "3":
            filename = input("Enter filename (e.g., mytokens.txt): ").strip()
            if not filename:
                print("No filename provided!")
                continue
            delay = input("Enter delay between checks in seconds (default 1.0): ").strip()
            delay = float(delay) if delay else 1.0
            checker.bulk_check_from_file(filename, delay)
            
        elif choice == "4":
            checker.load_results()
            if checker.results:
                print(f"\nLast {min(10, len(checker.results))} results:")
                for i, result in enumerate(checker.results[-10:], 1):
                    if result.get("valid"):
                        info = result.get("info", {})
                        print(f"{i}. ✓ {info.get('username', 'Unknown')}#{info.get('discriminator', '')}")
                    else:
                        print(f"{i}. ✗ {result.get('error', 'Invalid')}")
            else:
                print("No previous results found.")
                
        elif choice == "5":
            checker.export_to_csv()
            
        elif choice == "6":
            print("Exiting...")
            break
            
        else:
            print("Invalid option!")

if __name__ == "__main__":
    main()
