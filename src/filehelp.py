import os
import subprocess


class FileHelp:
    def __init__(self):
        pass

    @classmethod
    def is_blocked(cls, path: str) -> bool:
        """
        Checks if the file is loked for editing.
        """
        try:
            # Check if path exists.
            if not os.path.exists(path):
                raise Exception("File not found, please check the path and try again.")

            # Listing the file attributes.
            result = subprocess.run(
                ["lsattr", path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                text=True,
                check=True,
            )

            # If the file has 'i' attribute, it means that is locked for writing.
            return "i" in result.stdout[:21]

        except Exception as err:
            # TODO: adding logs
            print("Could not check status of the file: {err}")
            return False

    @classmethod
    def block(cls, path: str) -> bool:
        """
        Changes the file attribute to locked.
        """
        try:
            # Check if path exists.
            if not os.path.exists(path):
                raise Exception("File not found, please check the path and try again.")

            # Modify the file attribute.
            result = subprocess.run(
                ["sudo", "chattr", "+i", path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                text=True,
                check=True,
            )
            return True

        except Exception as err:
            # TODO: adding loggin
            print("Could not change the file attribute: {err}")
            return False

    @classmethod
    def unblock(cls, path: str) -> bool:
        """
        Changes the file attribute to unblock.
        """
        try:
            # Check if path exists.
            if not os.path.exists(path):
                raise Exception("File not found, please check the path and try again.")

            # Modify the file attribute.
            subprocess.run(
                ["sudo", "chattr", "-i", path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                text=True,
                check=True,
            )
            return True

        except Exception as err:
            # TODO: adding loggin
            print("Could not change the file attribute: {err}")
            return False


if __name__ == "__main__":
    print(FileHelp.is_blocked("/etc/resolv.conf"))
    FileHelp.block("/etc/resolv.conf")
    print(FileHelp.is_blocked("/etc/resolv.conf"))
