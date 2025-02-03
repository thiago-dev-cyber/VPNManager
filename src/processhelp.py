import subprocess


class ProcessHelp:
    """
    Class responsible for assisting process management.
    """

    @staticmethod
    def _finish_process(process_name: str):
        """
        Ends a certain process

        Args:
            process_name (str): Name of the process that will be closed.
        """
        try:
            subprocess.run(['sudo', 'killall', process_name], check=True)
        except subprocess.CalledProcessError:
            print(f'It was not possible to close the process {process_name}')
