#!/usr/bin/python3

#################################################################
# Basic file backup script written in python.                   #
#                                                               #
# Author: Marcus Uddenhed                                       #
# Version: 1.5.1                                                #
# Date: 2024-04-10                                              #
# Requirements:                                                 #
# pysftp for SFTP functions, only if vSendToSftp is set to yes. #
#                                                               #
#################################################################

## Global variables.
vBckDir: str = ""                      # Backup and temp folder to use during creation of compressed file or to store files locally.
vFilePrefix: str = ""                  # Name prefix of compressed file, _date and .zip is added at the end, ex. prefix_date.zip.
vKeepBackup: str = "no"                # Keep local backup files after sent to SFTP server, if no than nothing is kept locally.(no/yes)
vKeepDays: int = "20"                  # Days to keep if you want to keep certain days locally, relies on vKeepBackup.
vSendToSftp: str = "no"                # Should we send the file to a Sftp server.(no/yes)
vSftpUser: str = ""                    # User for remote server, used both with password or key file.
vSftpPass: str = ""                    # Password for remote server.
vSftpUseKey: str = "no"                # Use key file as authenticator against remote server for SFTP.
vSftpKeyFile: str = ""                 # Full path and key to use when connecting via key file instead of username/password.
vSftpDir: str = ""                     # Destination folder on remote server.
vSftpHost: str = ""                    # Remote server address.
vSftpPort: int = "22"                  # Remote server port.
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
import os## Module imports.
from datetime import datetime
from time import time
import zipfile
import os

#### Script Action

## Import pysftp only if vSendToSftp set to yes.
if vSendToSftp == "yes":
  import pysftp

## Import subprocess only if vPreBckCmd or vPostBckCmd set to yes.
if vPreBckCmd == "yes" or vPostBckCmd == "yes":
  import subprocess

## Get current date
def funcDateString() -> datetime:
  # Returns the today string year, month, day.
  return datetime.now().strftime("%Y%m%d")

## Define function for Pre OS commands.
def funcExecutePreOsCmd(vPreOsCmd: list) -> None:
  try:
    if vPreBckCmd.casefold() == "yes":
      # iterate through each specified command.
      for vExecute in vPreOsCmd:
        subprocess.run(vExecute, shell=True, check=True)
      # Send info to console.
      print("OS commands has been executed...")
  except:
    # Send info to console.
    print("Could not execute OS command...")

## Define function for Pre OS commands.
def funcExecutePostOsCmd(vPostOsCmd: list) -> None:
  try:
    if vPostBckCmd.casefold() == "yes":
      # iterate through each specified command.
      for vExecute in vPostOsCmd:
        subprocess.run(vExecute, shell=True, check=True)
      # Send info to console.
      print("OS commands has been executed...")
  except:
    # Send info to console.
    print("Could not execute OS command...")

## Build Zip filename with path.
vSetZipFile: str = os.path.join(vBckDir, vFilePrefix + "_" + funcDateString() + ".zip")

## Define function for compressing files/folders into a zip file.
def funcCreateZipFile(vZipName: str, vPath: str) -> None:
  try:
    # Send info to console.
    print("Creating Zip file...")
    # Parameters: vZipName - name of the zip file; path - name of folder/file to be put in zip file.
    vZipFile: str = zipfile.ZipFile(vZipName, 'w', zipfile.ZIP_DEFLATED)
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
  except:
    # Send info to console.
    print("Could not create Zip file...")

## Define function send to SFTP.
def funcSendToSftp(vFile: str) -> None:
  try:
    if vSendToSftp.casefold() == "yes":
      # Send info to console.
      print("Sending Zip file to SFTP server...")
      # Convert port to integer, needed since we use "" above to keep it a bit more tidy.
      vIntPort: int = int(vSftpPort)
      # Check connection parameters and build connection string.
      if vSftpUseKey.lower() == "yes":
        # Connect to SFTP with key fil and upload file.
        with pysftp.Connection(host=vSftpHost, port=vIntPort, username=vSftpUser, private_key=vSftpKeyFile) as sftp:
          # Change directory.
          with sftp.cd(vSftpDir):
            # Upload file
            sftp.put(vFile)
      elif vSftpUseKey.lower() == "no":
        # Connect to SFTP with username/password and upload file.
        with pysftp.Connection(host=vSftpHost, port=vIntPort, username=vSftpUser, password=vSftpPass) as sftp:
          # Change directory.
          with sftp.cd(vSftpDir):
            # Upload file
            sftp.put(vFile)
    # Send info to console.
    print("Uploaded: ", vFile)
    print("Done sending Zip file to SFTP server...")
  except:
      # Send info to console.
      print("Could not connect to server or upload file...")

## Define history function.
def funcKeepBackup(vGetDays: int, vGetDir: str) -> None:
  try:
    # Check if to keep a history or not.
    vIntDays: int = int(vGetDays)
    if vKeepBackup.casefold() == "yes":
      # Send info to console.
      print("Pruning backup folder, keeping", vIntDays, "days...")
      # Set today as current day.
      vTimeNow: int = time()
      # Remove files based on days to keep.
      for fname in os.listdir(vGetDir):
        if fname.startswith(vFilePrefix):
          if os.path.getmtime(os.path.join(vGetDir, fname)) < vTimeNow - vIntDays * 86400:
            os.remove(os.path.join(vGetDir, fname))
      # Send info to console.
      print("Done pruning backup folder...")
    elif vKeepBackup.casefold() == "no":
      # Send info to console.
      print("Removing all local backup files...")
      # Build file list and remove files.
      vSetFilePattern: str = os.path.join(vFilePrefix + "_")
      for fname in os.listdir(vGetDir):
        if fname.startswith(vSetFilePattern):
          os.remove(os.path.join(vGetDir, fname))
    # Send info to console.
    print("Done removing all local backup files...")
  except:
    # Send info to console.
    print("Could not clean backup folder...")

## Call the pre OS command function and run only if vPreBckCmd is set to yes.
funcExecutePreOsCmd(vPreOsCmd)

## Call the backup function and create the backup.
funcCreateZipFile(vSetZipFile, vSrcDir)

## Call the Sftp function and upload file only if vSendToSftp is set to yes.
funcSendToSftp(vSetZipFile)

## Call the post OS command function and run only if vPostBckCmd is set to yes.
funcExecutePostOsCmd(vPostOsCmd)

## Call the history function to enable automatic housekeeping in the backup folder.
funcKeepBackup(vKeepDays, vBckDir)
