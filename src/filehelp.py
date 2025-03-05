import os
import random
import subprocess


class FileHelp:
    """
    A utility class for managing file attributes and content.
    Provides methods to check, lock, unlock, and write to files,
    as well as retrieve a random file from a directory.
    """

    @staticmethod
    def is_blocked(path: str) -> bool:
        """
        Checks if the file is locked for editing (immutable attribute set).

        Args:

            path (str): Path to the file.

        Return:
        s
            True if the file is locked, False otherwise.
        """
        try:
            if not os.path.exists(path):
                raise FileNotFoundError(
                    f"File '{path}' not found. Please check the path and try again."
                )

            result = subprocess.run(
                ['lsattr', path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                text=True,
                check=True,
            )
            return 'i' in result.stdout[:21]

        except FileNotFoundError as e:
            print(f'Error: {e}')

        except subprocess.SubprocessError:
            print(
                f"Error: Unable to retrieve file attributes for '{path}'."
                + " Ensure 'lsattr' is available."
            )

        except Exception as e:
            print(f'Unexpected error: {e}')

        return False

    @staticmethod
    def block(path: str) -> bool:
        """
        Locks the file by setting it as immutable.

        Args:

            path (str): Path to the file.

        Return:

            True if the operation was successful, False otherwise.
        """
        try:
            if not os.path.exists(path):
                raise FileNotFoundError(
                    f"File '{path}' not found. Please check the path and try again."
                )

            subprocess.run(['chattr', '+i', path], check=True)
            return True

        except FileNotFoundError as e:
            print(f'Error: {e}')
        except subprocess.SubprocessError:
            print(
                f"Error: Failed to lock file '{path}'."
                + 'Ensure you have the required permissions.'
            )
        except Exception as e:
            print(f'Unexpected error: {e}')

        return False

    @staticmethod
    def unblock(path: str) -> bool:
        """
        Unlocks the file by removing the immutable attribute.

        Args:

            path (str): Path to the file.

        Return:

            True if the operation was successful, False otherwise.
        """
        try:
            if not os.path.exists(path):
                raise FileNotFoundError(
                    f"File '{path}' not found. Please check the path and try again."
                )

            subprocess.run(['chattr', '-i', path], check=True)
            return True

        except FileNotFoundError as e:
            print(f'Error: {e}')
        except subprocess.SubprocessError:
            print(
                f"Error: Failed to unlock file '{path}'."
                + ' Ensure you have the required permissions.'
            )
        except Exception as e:
            print(f'Unexpected error: {e}')

        return False

    @staticmethod
    def write(path: str, data: str) -> bool:
        """
        Writes data to a file. If the file is locked, it unlocks it before writing,
        then re-locks it after writing.

        Args:

            path (str): Path to the file.
            data (str): Data to write into the file.

        Returns:

            True if the write operation was successful, False otherwise.
        """
        try:
            if FileHelp.is_blocked(path):
                FileHelp.unblock(path)

            with open(path, 'w') as file:
                file.write(data)

            FileHelp.block(path)
            return True

        except FileNotFoundError as e:
            print(f'Error: {e}')
        except OSError:
            print(
                f"Error: Unable to write to '{path}'."
                + 'Check permissions and available space.'
            )
        except Exception as e:
            print(f'Unexpected error: {e}')

        return False

    @staticmethod
    def get_random_file(path: str) -> str | None:
        """
        Retrieves a random file from the specified directory.

        Args:

            path (str): Path to the directory.

        Return:

            Path to a randomly selected file, or None if no files are found.
        """
        try:
            if not os.path.exists(path) or not os.path.isdir(path):
                raise FileNotFoundError(
                    f"Directory '{path}' not found. Please check the path entered."
                )

            files = [
                os.path.join(path, f)
                for f in os.listdir(path)
                if os.path.isfile(os.path.join(path, f))
            ]
            if not files:
                raise FileNotFoundError(f"No files found in the directory '{path}'.")

            return random.choice(files)

        except FileNotFoundError as e:
            print(f'Error: {e}')
        except Exception as e:
            print(f'Unexpected error: {e}')

        return None
