#!/usr/bin/python3

###################################################################
# Basic file backup script written in python.                     #
#                                                                 #
# Author: Marcus Uddenhed                                         #
# Version: 1.6.0                                                  #
# Date: 2025-10-02                                                #
# Requirements:                                                   #
# paramiko for SFTP functions, only if vSendToSftp is set to yes. #
#                                                                 #
###################################################################

## Global variables.
vBckDir: str = ""                      # Backup and temp folder to use during creation of compressed file or to store files locally.
vFilePrefix: str = ""                  # Name prefix of compressed file, _date and .zip is added at the end, ex. prefix_date.zip.
vKeepBackup: str = "no"                # Keep local backup files after sent to SFTP server, if no than nothing is kept locally.(no/yes)
vKeepDays: str = "20"                  # Days to keep if you want to keep certain days locally, relies on vKeepBackup.
vSendToSftp: str = "no"                # Should we send the file to a Sftp server.(no/yes)
vSftpUser: str = ""                    # User for remote server, used both with password or key file.
vSftpPass: str = ""                    # Password for remote server.
vSftpUseKey: str = "no"                # Use key file as authenticator against remote server for SFTP.
vSftpKeyFile: str = ""                 # Full path and key to use when connecting via key file instead of username/password.
vSftpDir: str = ""                     # Destination folder on remote server.
vSftpHost: str = ""                    # Remote server address.
vSftpPort: str = "22"                  # Remote server port.
vPreBckCmd: str = "no"                 # Run extra OS specific commands before backup/zip.(no/yes)
vPostBckCmd: str = "no"                # Run extra OS specific commands after backup/zip.(no/yes)

# Folders to backup, this can be a single path or an list of paths, like this: ["/singlepath"] or ["/path1","path2"] and so on.
vSrcDir: list = [""]

# External OS commands to execute before compressing to zip, be sure to put the output folder to vSrcDir if it is to be added to zip file.
vPreOsCmd: list = [""]

# External OS commands to execute after compressing to zip.
vPostOsCmd: list = [""]

#### Do not edit anything below this line ####

## Module imports.
from datetime import datetime
from time import time
import zipfile
import os

#### Script Action

## Import pysftp only if vSendToSftp set to yes.
if vSendToSftp == "yes":
  import paramiko

## Import subprocess only if vPreBckCmd or vPostBckCmd set to yes.
if vPreBckCmd == "yes" or vPostBckCmd == "yes":
  import subprocess

## Define function - Get current date
def funcDateString() -> str:
  # Returns the today string year, month, day.
  return datetime.now().strftime("%Y%m%d")

## Define function - Pre OS commands.
def funcExecutePreOsCmd(vPreOsCmd: list) -> None:
  try:
    if vPreBckCmd.casefold() == "yes":
      # iterate through each specified command.
      for vExecute in vPreOsCmd:
        subprocess.run(vExecute, shell=True, check=True) # type: ignore
      # Send info to console.
      print("OS commands has been executed...")
  except Exception as vErr:
    # Send info to console and exit.
    print("Could not execute OS command...")
    print(vErr)
    exit(1)

## Define function - Post OS commands.
def funcExecutePostOsCmd(vPostOsCmd: list) -> None:
  try:
    if vPostBckCmd.casefold() == "yes":
      # iterate through each specified command.
      for vExecute in vPostOsCmd:
        subprocess.run(vExecute, shell=True, check=True) # type: ignore
      # Send info to console.
      print("OS commands has been executed...")
  except Exception as vErr:
    # Send info to console and exit.
    print("Could not execute OS command...")
    print(vErr)
    exit(1)

## Build Zip filename with path and without full path.
vSetZipFileName: str = vFilePrefix + "_" + funcDateString() + ".zip"
vSetZipFileFullPath: str = os.path.join(vBckDir, vSetZipFileName)

## Define function - Compressing files/folders into a zip file.
def funcCreateZipFile(vZipName: str, vPath: list[str]) -> None:
  try:
    # Send info to console.
    print("Creating Zip file...")
    # Parameters: vZipName - name of the zip file; path - name of folder/file to be put in zip file.
    vZipFile: object = zipfile.ZipFile(vZipName, 'w', zipfile.ZIP_DEFLATED)
    # iterate through each specified folder.
    for vFolder in vPath:
      # Changes root dir to given input folder to make zipped files relative to that.
      os.chdir(vFolder)
      # Send each folder and file to zip file.
      for root, dirs, files in os.walk(vFolder, topdown=False):
        for name in files:
          vZipFile.write(os.path.join(root, name))
    # Close the Zip file.
    vZipFile.close()
    # Send info to console.
    print("Zip file has been created...")
  except Exception as vErr:
    # Send info to console and exit.
    print("Could not create Zip file...")
    print(vErr)
    exit(1)

## Define function - Connect to SFTP.
def funcSftpConnect() -> None:
  try:
    global vScpClient
    vScpClient = paramiko.SSHClient() # type: ignore
    vScpClient.load_system_host_keys()
    vInputPortInt: int = int(vSftpPort)
    # Check if to ask for username & password or to use keyfile.
    if vSftpUseKey.lower() == "no":
      print('Entering Username & Password for remote server...')
      vScpClient.connect(vSftpHost, port=vInputPortInt, username=vSftpUser, password=vSftpPass)
    elif vSftpUseKey.lower() == "yes":
      # Get KeyFile.
      vKeyFile: str = paramiko.RSAKey.from_private_key_file(vSftpKeyFile) # type: ignore
      # Check if username is entered, if yes combine with key file, else use only key file.
      if vSftpUser != "":
        print('Using Username & KeyFile to connect to remote server...')
        vScpClient.connect(vSftpHost, port=vInputPortInt, username=vSftpUser, pkey=vKeyFile, look_for_keys=False) # type: ignore
      else:
        print('Using KeyFile to connect to remote server...')
        vScpClient.connect(vSftpHost, port=vInputPortInt, pkey=vKeyFile, look_for_keys=False) # type: ignore
    # Open connection
    global vScpConn
    vScpConn = vScpClient.open_sftp()
    print('Connected to SFTP...')
  except Exception as vErr:
    # Send info to console and exit.
    print('Cannot connect to remote server, exiting...')
    print(vErr)
    exit(1)

## Define function - Send to SFTP.
def funcSendToSftp() -> None: #vShowMsg: str) -> None:
  try:
    # Open SFTP connection.
    funcSftpConnect()
    # Send file.
    print('Sending file: ' + vSetZipFileName + ' To ' + vSftpDir + ' folder...')
    vScpConn.chdir(vSftpDir)
    vScpConn.put(vSetZipFileFullPath, vSetZipFileName)
    print('Sent Ok...')
    # Close SFTP connection.
    funcSftpClose()
  except Exception as vErr:
    print('Could not send file...')
    # Close SFTP Connection.
    funcSftpClose()
    # Send info to console and exit.
    print(vErr)
    exit(1)

## Define function - Close SFTP connection.
def funcSftpClose() -> None:
  try:
    # Close active session if any.
    print("Closing remote session...")
    vScpConn.close()
    print("Remote session closed...")
  except Exception as vErr:
    # Send info to console and exit.
    print(vErr)
    exit(1)

## Define function - Keep history.
def funcKeepBackup(vGetDays: str, vGetDir: str) -> None:
  try:
    # Check if to keep a history or not.
    vIntDays: int = int(vGetDays)
    if vKeepBackup.casefold() == "yes":
      # Send info to console.
      print("Pruning backup folder, keeping", vIntDays, "days...")
      # Set today as current day.
      vTimeNow: int = int(time())
      # Remove files based on days to keep.
      for fname in os.listdir(vGetDir):
        if fname.startswith(vFilePrefix):
          if os.path.getmtime(os.path.join(vGetDir, fname)) < vTimeNow - vIntDays * 86400:
            os.remove(os.path.join(vGetDir, fname))
      # Send info to console.
      print("Done pruning backup folder...")
    elif vKeepBackup.casefold() == "no":
      # Check if we are sending them to remote location.
      if vSendToSftp.casefold() == "no":
        print("WARNING!!")
        print("---------")
        print("removing all local files without sending them to SFTP defeats the purpose of this script.")
        print("Either send to remote location or use pruning to keep set amount of local backups")
        print("Will not remove backup file(s)...")
        print("---------")
        exit(0)
      elif vSendToSftp.casefold() == "yes":
        # Send info to console.
        print("Removing all local backup files...")
        # Build file list and remove files.
        vSetFilePattern: str = os.path.join(vFilePrefix + "_")
        for fname in os.listdir(vGetDir):
          if fname.startswith(vSetFilePattern):
            os.remove(os.path.join(vGetDir, fname))
        # Send info to console.
        print("Done removing all local backup files...")
  except Exception as vErr:
    # Send info to console and exit.
    print("Could not clean backup folder...")
    print(vErr)
    exit(1)

#### Execute functions ####

## Call the pre OS command function and run only if vPreBckCmd is set to yes.
funcExecutePreOsCmd(vPreOsCmd)

## Call the backup function and create the backup.
funcCreateZipFile(vSetZipFileFullPath, vSrcDir)

## Call the Sftp functions and upload file only if vSendToSftp is set to yes.
funcSendToSftp()

## Call the post OS command function and run only if vPostBckCmd is set to yes.
funcExecutePostOsCmd(vPostOsCmd)

## Call the history function to enable automatic housekeeping in the backup folder.
funcKeepBackup(vKeepDays, vBckDir)
