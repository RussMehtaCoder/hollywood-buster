import json
from pathlib import Path

class FollowerAnalyzer:
    """
    """

    def __init__(self, followers: list[dict], following: list[dict], output_dir: str = "."):
        self.followers = followers
        self.following = following
        self.output_dir = Path(output_dir)

        # Precompute username sets for quick comparison
        self.followers_usernames = {item["username"] for item in followers}
        self.following_usernames = {item["username"] for item in following}

        # Containers for computed results
        self.they_dont_follow_back = []
        self.you_dont_follow_back = []
        # self.follow_each_other = []

    # --------------------------
    # Computation Methods
    # --------------------------

    def compute_they_dont_follow_back(self):
        """Find accounts you follow that don't follow you back."""
        self.they_dont_follow_back = [
            user for user in self.following if user["username"] not in self.followers_usernames
        ]
        print(f"[info] They don't follow you back: {len(self.they_dont_follow_back)}")
        return self.they_dont_follow_back

    def compute_you_dont_follow_back(self):
        """Find accounts that follow you, but you don't follow back."""
        self.you_dont_follow_back = [
            user for user in self.followers if user["username"] not in self.following_usernames
        ]
        # print(f"[info] You don't follow them back: {len(self.you_dont_follow_back)}")
        return self.you_dont_follow_back

    # def compute_follow_each_other(self):
    #     """Find accounts where both follow each other (mutuals)."""
    #     mutual_usernames = self.followers_usernames & self.following_usernames
    #     self.follow_each_other = [
    #         user for user in self.followers if user["username"] in mutual_usernames
    #     ]
    #     # print(f"[info] Follow each other: {len(self.follow_each_other)}")
    #     return self.follow_each_other

    # --------------------------
    # Save Helpers
    # --------------------------

    def _save_json(self, filename: str, data: list[dict]):
        """Internal helper to safely write JSON output."""
        file_path = self.output_dir / filename
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            print(f"[ok] Wrote {len(data)} records to {filename}")
        except Exception as e:
            print(f"[error] Failed to write {filename}: {e}")

    def save_all(self):
        """Save all computed results to disk."""
        if self.they_dont_follow_back:
            self._save_json("they_dont_follow_back.json", self.they_dont_follow_back)
        if self.you_dont_follow_back:
            self._save_json("you_dont_follow_back.json", self.you_dont_follow_back)
        if self.follow_each_other:
            self._save_json("follow_each_other.json", self.follow_each_other)

    # --------------------------
    # Summary
    # --------------------------

    def summary(self):
        """Print a summary of all results."""
        print("\n[summary]")
        print(f"  They don't follow you back: {len(self.they_dont_follow_back)}")
        print(f"  You don't follow them back: {len(self.you_dont_follow_back)}")
        print(f"  Follow each other: {len(self.follow_each_other)}\n")
