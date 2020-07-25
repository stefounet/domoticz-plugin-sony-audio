#       
#       Sony Audio Plugin for Domoticz
#       Author: Stefounet, 2020
#       
"""
<plugin key="SonyAudio" name="Sony Audio Receiver" author="stefounet" version="1.0" wikilink="https://github.com/stefounet/domoticz-plugin-sony-audio" externallink="https://developer.sony.com/develop/audio-control-api/api-references/api-overview-2">
    <description>
Sony Audio Receiver plugin for Domoticz.<br/><br/>
Prerequisites:<br/>
* Enable WOL on your Sony Receiver : [Settings] => [Network] => [Home Network Setup] => [Remote Start] => [On]<br/>
* Give your TV a static IP address, or make a DHCP reservation for a specific IP address in your router.<br/>
* Determine the MAC address of your TV: [Settings] => [Network] => [Network Setup] => [View Network Status]<br/>
    </description>
    <params>
        <param field="Address" label="IP address" width="200px" required="true"/>
        <param field="Mode1" label="Startup Delay" width="50px" required="true">
            <options>
                <option label="1" value="1"/>
                <option label="5" value="5"/>
                <option label="10" value="10"/>
                <option label="20" value="20"/>
                <option label="30" value="30"/>
                <option label="40" value="40" default="true" />
                <option label="60" value="60"/>
            </options>
        </param>
        <param field="Mode2" label="MAC address" width="200px" required="true" default="AA:BB:CC:DD:EE:FF"/>
        <param field="Mode3" label="Volume bar" width="75px">
            <options>
                <option label="True" value="Volume"/>
                <option label="False" value="Fixed" default="true" />
            </options>
        </param>
        <param field="Mode4" label="Sources" width="550px" required="true" default="Off|AppleTV|FM|TV|Domolyon|Airplay"/>
        <param field="Mode5" label="Update interval (sec)" width="30px" required="true" default="30"/>
        <param field="Mode6" label="Debug" width="75px">
            <options>
                <option label="True" value="Debug"/>
                <option label="False" value="Normal" default="true" />
            </options>
        </param>
    </params>
</plugin>
"""
import Domoticz
import socket
import struct
import datetime

def _wakeonlan(self):
    if self._mac is not none:
        addr_byte = self._mac.split(':')
        hw_addr = struct.pack('bbbbbb', int(addr_byte[0], 16),
                              int(addr_byte[1], 16),
                              int(addr_byte[2], 16),
                              int(addr_byte[3], 16),
                              int(addr_byte[4], 16),
                              int(addr_byte[5], 16))
        msg = b'\xff' * 6 + hw_addr * 16
        socket_instance = socket.socket(socket.af_inet, socket.sock_dgram)
        socket_instance.setsockopt(socket.sol_socket, socket.so_broadcast,
                                   1)
        socket_instance.sendto(msg, ('<broadcast>', 9))
        socket_instance.close()

class BasePlugin:
    powerOn = False
    #ar stands for Audio Receiver
    arState = 0
    arMainVolume = 0
    arMainSource = 0
    arPlaying = {}
    SourceOptions = {}
    SonyConn = None
    
    # Executed once at reboot/update, can create up to 255 devices
    def onStart(self):
        global _ar
        
        if Parameters["Mode6"] == "Debug":
            Domoticz.Debugging(1)
            DumpConfigToLog()

        self.SourceOptions = {'LevelActions': '|'*Parameters["Mode4"].count('|'),
                             'LevelNames': Parameters["Mode4"],
                             'LevelOffHidden': 'false',
                             'SelectorStyle': '1'}

        if (len(Devices) == 0):
            Domoticz.Device(Name="Power", Unit=1, TypeName="Switch",  Image=5).Create()
            Domoticz.Device(Name="Main Zone", Unit=2, TypeName="Selector Switch", Switchtype=18, Image=5, Options=self.SourceOptions).Create()
            Domoticz.Device(Name="Main Volume", Unit=3, Type=244, Subtype=73, Switchtype=7, Image=8).Create()

        return True
         
                                    
"""        if len(Devices) == 0:
            Domoticz.Device(Name="Status", Unit=1, Type=17, Image=2, Switchtype=17, Used=1).Create()
            if Parameters["Mode3"] == "Volume": Domoticz.Device(Name="Volume", Unit=2, Type=244, Subtype=73, Switchtype=7, Image=8, Used=1).Create()
            Domoticz.Device(Name="Source", Unit=3, TypeName="Selector Switch", Switchtype=18, Image=2, Options=self.SourceOptions3, Used=1).Create()
            Domoticz.Device(Name="Control", Unit=4, TypeName="Selector Switch", Switchtype=18, Image=2, Options=self.SourceOptions4, Used=1).Create()
            Domoticz.Device(Name="Channel", Unit=5, TypeName="Selector Switch", Switchtype=18, Image=2, Options=self.SourceOptions5, Used=1).Create()
            Domoticz.Log("Devices created")
        elif Parameters["Mode3"] == "Volume" and 2 not in Devices:
            Domoticz.Device(Name="Volume", Unit=2, Type=244, Subtype=73, Switchtype=7, Image=8, Used=1).Create()
            Domoticz.Log("Volume device created")
        elif Parameters["Mode3"] != "Volume" and 2 in Devices:
            Devices[2].Delete()
            Domoticz.Log("Volume device deleted")
        elif 1 not in Devices:
            Domoticz.Device(Name="Status", Unit=1, Type=17, Image=2, Switchtype=17, Used=1).Create()
            Domoticz.Log("TV device created")
        elif 3 not in Devices:
            Domoticz.Device(Name="Source", Unit=3, TypeName="Selector Switch", Switchtype=18, Image=2, Options=self.SourceOptions3, Used=1).Create()
            Domoticz.Log("Source device created")
        elif 4 not in Devices:
            Domoticz.Device(Name="Control", Unit=4, TypeName="Selector Switch", Switchtype=18, Image=2, Options=self.SourceOptions4, Used=1).Create()
            Domoticz.Log("Control device created")
        elif 5 not in Devices:
            Domoticz.Device(Name="Channel", Unit=5, TypeName="Selector Switch", Switchtype=18, Image=2, Options=self.SourceOptions5, Used=1).Create()
            Domoticz.Log("Channel device created")
        else:
            if 1 in Devices: self.tvState = Devices[1].nValue    #--> of sValue
            if 2 in Devices: self.tvVolume = Devices[2].nValue   #--> of sValue
            if 3 in Devices: self.tvSource = Devices[3].sValue
            if 4 in Devices: self.tvControl = Devices[4].sValue
            if 5 in Devices: self.tvChannel = Devices[5].sValue
        
        # Set update interval, values below 10 seconds are not allowed due to timeout of 5 seconds in bravia.py script
        updateInterval = int(Parameters["Mode5"])
        if updateInterval < 30:
            if updateInterval < 10: updateInterval == 10
            Domoticz.Log("Update interval set to " + str(updateInterval) + " (minimum is 10 seconds)")
            Domoticz.Heartbeat(updateInterval)
        else:
            Domoticz.Heartbeat(30)

        return #--> return True
"""    
    # Executed each time we click on device through Domoticz GUI
    def onCommand(self, Unit, Command, Level, Hue):
        Domoticz.Log("onCommand called for Unit " + str(Unit) + ": Parameter '" + str(Command) + "', Level: " + str(Level))

        Command = Command.strip()
        action, sep, params = Command.partition(' ')
        action = action.capitalize()
        params = params.capitalize()
       
        if self.powerOn == False:
            if Unit == 1:     # TV power switch
                if action == "On":
                    # Start TV when WOL is not available, only works on Android
                    if Parameters["Mode2"] == "Android":
                        Domoticz.Log("No MAC address configured, TV will be started with setPowerStatus command (Android only)")
                        try:
                            _tv.turn_on_command()
                            self.tvPlaying = "TV starting" # Show that the TV is starting, as booting the TV takes some time
                            self.SyncDevices()
                        except Exception as err:
                            Domoticz.Log("Error when starting TV with set PowerStatus, Android only (" +  str(err) + ")")
                    # Start TV using WOL
                    else:
                        try:
                            _tv.turn_on()
                            self.tvPlaying = "TV starting" # Show that the TV is starting, as booting the TV takes some time
                            self.SyncDevices()
                        except Exception as err:
                            Domoticz.Log("Error when starting TV using WOL (" +  str(err) + ")")
        else:
            if Unit == 1:     # TV power switch
                if action == "Off":
                    _tv.turn_off()
                    self.tvPlaying = "Off"
                    self.SyncDevices()
                # Remote buttons (action is capitalized so chosen for Command)
                elif Command == "ChannelUp": _tv.send_req_ircc("AAAAAQAAAAEAAAAQAw==")       # ChannelUp
                elif Command == "ChannelDown": _tv.send_req_ircc("AAAAAQAAAAEAAAARAw==")     # ChannelDown
                elif Command == "Channels": _tv.send_req_ircc("AAAAAQAAAAEAAAA6Aw==")        # Display, shows information on what is playing
                elif Command == "VolumeUp": _tv.send_req_ircc("AAAAAQAAAAEAAAASAw==")        # VolumeUp
                elif Command == "VolumeDown": _tv.send_req_ircc("AAAAAQAAAAEAAAATAw==")      # VolumeDown
                elif Command == "Mute": _tv.send_req_ircc("AAAAAQAAAAEAAAAUAw==")            # Mute
                elif Command == "Select": _tv.send_req_ircc("AAAAAQAAAAEAAABlAw==")          # Confirm
                elif Command == "Up": _tv.send_req_ircc("AAAAAQAAAAEAAAB0Aw==")              # Up
                elif Command == "Down": _tv.send_req_ircc("AAAAAQAAAAEAAAB1Aw==")            # Down
                elif Command == "Left": _tv.send_req_ircc("AAAAAQAAAAEAAAA0Aw==")            # Left
                elif Command == "Right": _tv.send_req_ircc("AAAAAQAAAAEAAAAzAw==")           # Right
                elif Command == "Home": _tv.send_req_ircc("AAAAAQAAAAEAAABgAw==")            # Home
                elif Command == "Info": _tv.send_req_ircc("AAAAAgAAAKQAAABbAw==")            # EPG
                elif Command == "Back": _tv.send_req_ircc("AAAAAgAAAJcAAAAjAw==")            # Return
                elif Command == "ContextMenu": _tv.send_req_ircc("AAAAAgAAAJcAAAA2Aw==")     # Options
                elif Command == "FullScreen": _tv.send_req_ircc("AAAAAQAAAAEAAABjAw==")      # Exit
                elif Command == "ShowSubtitles": _tv.send_req_ircc("AAAAAQAAAAEAAAAlAw==")   # Input
                elif Command == "Stop": _tv.send_req_ircc("AAAAAgAAAJcAAAAYAw==")            # Stop
                elif Command == "BigStepBack": _tv.send_req_ircc("AAAAAgAAAJcAAAAZAw==")     # Pause
                elif Command == "Rewind": _tv.send_req_ircc("AAAAAgAAAJcAAAAbAw==")          # Rewind
                elif Command == "PlayPause": _tv.send_req_ircc("AAAAAgAAABoAAABnAw==")       # TV pause
                elif Command == "FastForward": _tv.send_req_ircc("AAAAAgAAAJcAAAAcAw==")     # Forward
                elif Command == "BigStepForward": _tv.send_req_ircc("AAAAAgAAAJcAAAAaAw==")  # Play
                    
            if Unit == 2:     # TV volume
                if action == 'Set':
                    self.tvVolume = str(Level)
                    _tv.set_volume_level(self.tvVolume)
                elif action == "Off":
                    _tv.mute_volume()
                    UpdateDevice(2, 0, str(self.tvVolume))
                elif action == "On":
                    _tv.mute_volume()
                    UpdateDevice(2, 1, str(self.tvVolume))
                    
            if Unit == 3:   # TV source
                if Command == 'Set Level':
                    if Level == 10:
                        _tv.send_req_ircc("AAAAAQAAAAEAAAAAAw==") #TV Num1
                        self.GetTVInfo()
                    if Level == 20:
                        _tv.send_req_ircc("AAAAAgAAABoAAABaAw==") #HDMI1
                        self.tvPlaying = "HDMI 1"
                    if Level == 30:
                        _tv.send_req_ircc("AAAAAgAAABoAAABbAw==") #HDMI2
                        self.tvPlaying = "HDMI 2"
                    if Level == 40:
                        _tv.send_req_ircc("AAAAAgAAABoAAABcAw==") #HDMI3
                        self.tvPlaying = "HDMI 3"
                    if Level == 50:
                        _tv.send_req_ircc("AAAAAgAAABoAAABdAw==") #HDMI4
                        self.tvPlaying = "HDMI 4"
                    if Level == 60:
                        _tv.send_req_ircc("AAAAAgAAABoAAAB8Aw==") #Netflix
                        self.tvPlaying = "Netflix"
                    self.tvSource = Level
                    self.SyncDevices()
                        
            if Unit == 4:   # TV control
                if Command == 'Set Level':
                    if Level == 10: _tv.send_req_ircc("AAAAAgAAAJcAAAAaAw==") #Play
                    if Level == 20: _tv.send_req_ircc("AAAAAgAAAJcAAAAYAw==") #Stop
                    if Level == 30: _tv.send_req_ircc("AAAAAgAAAJcAAAAZAw==") #Pause
                    if Level == 40: _tv.send_req_ircc("AAAAAgAAABoAAABnAw==") #Pause TV
                    if Level == 50: _tv.send_req_ircc("AAAAAQAAAAEAAABjAw==") #Exit
                    self.tvControl = Level
                    self.SyncDevices()
            
            if Unit == 5:   # TV channels
                if Command == 'Set Level':
                    if Level == 10: _tv.send_req_ircc("AAAAAQAAAAEAAAAAAw==") #1
                    if Level == 20: _tv.send_req_ircc("AAAAAQAAAAEAAAABAw==") #2
                    if Level == 30: _tv.send_req_ircc("AAAAAQAAAAEAAAACAw==") #3
                    if Level == 40: _tv.send_req_ircc("AAAAAQAAAAEAAAADAw==") #4
                    if Level == 50: _tv.send_req_ircc("AAAAAQAAAAEAAAAEAw==") #5
                    if Level == 60: _tv.send_req_ircc("AAAAAQAAAAEAAAAFAw==") #6
                    if Level == 70: _tv.send_req_ircc("AAAAAQAAAAEAAAAGAw==") #7
                    if Level == 80: _tv.send_req_ircc("AAAAAQAAAAEAAAAHAw==") #8
                    if Level == 90: _tv.send_req_ircc("AAAAAQAAAAEAAAAIAw==") #9
                    # Level 100 = --Choose a channel--
                    self.tvChannel = Level
                    self.SyncDevices()
        
        return

    # Execution depend of Domoticz.Heartbeat(x) x in seconds
    def onHeartbeat(self):
        try:
            tvStatus = _tv.get_power_status()
            Domoticz.Debug("Status TV: " + str(tvStatus))
        except Exception as err:
            Domoticz.Log("Not connected to TV (" +  str(err) + ")")

        if tvStatus == 'active':                        # TV is on
            self.powerOn = True
            try:
                self.GetTVInfo()
            except Exception as err:
                Domoticz.Error("No data received from TV, probably it has just been turned off (" +  str(err) + ")")
        else:                                           # TV is off or standby
            self.powerOn = False
            self.SyncDevices()

        return

    def SyncDevices(self):
        # TV is off
        if self.powerOn == False:
            if self.tvPlaying == "TV starting":         # TV is booting and not yet responding to get_power_status
                UpdateDevice(1, 1, self.tvPlaying)
                #UpdateDevice(3, 1, self.tvSource)
            else:                                       # TV is off so set devices to off
                self.ClearDevices()
        # TV is on
        else:
            if self.tvPlaying == "Off":                 # TV is set to off in Domoticz, but self.powerOn is still true
                self.ClearDevices()
            else:                                       # TV is on so set devices to on
                if not self.tvPlaying:
                    Domoticz.Debug("No information from TV received (TV was paused and then continued playing from disk) - SyncDevices")
                else:
                    UpdateDevice(1, 1, self.tvPlaying)
                    UpdateDevice(3, 1, str(self.tvSource))
                if Parameters["Mode3"] == "Volume": UpdateDevice(2, 2, str(self.tvVolume))
                UpdateDevice(4, 1, str(self.tvControl))
                UpdateDevice(5, 1, str(self.tvChannel))

        return
    
    def ClearDevices(self):
        self.tvPlaying = "Off"
        UpdateDevice(1, 0, self.tvPlaying)          #Status
        if Parameters["Mode3"] == "Volume": UpdateDevice(2, 0, str(self.tvVolume))  #Volume
        self.tvSource = 0
        self.tvControl = 0
        self.tvChannel = 0
        UpdateDevice(3, 0, str(self.tvSource))      #Source
        UpdateDevice(4, 0, str(self.tvControl))     #Control
        UpdateDevice(5, 0, str(self.tvChannel))     #Channel
        
        return
    
    def GetTVInfo(self):
        self.tvPlaying = _tv.get_playing_info()
        if not self.tvPlaying:                              # Dict is empty
            Domoticz.Debug("No information from TV received (TV was paused and then continued playing from disk)")
        else:
            if self.tvPlaying['programTitle'] != None:      # Get information on channel and program title if tuner of TV is used
                if self.tvPlaying['startDateTime'] != None: # Show start time and end time of program
                    self.startTime, self.endTime, self.perc_playingTime = _tv.playing_time(self.tvPlaying['startDateTime'], self.tvPlaying['durationSec'])
                    self.tvPlaying = str(int(self.tvPlaying['dispNum'])) + ': ' + self.tvPlaying['title'] + ' - ' + self.tvPlaying['programTitle'] + ' [' + str(self.startTime) + ' - ' + str(self.endTime) +']'
                    Domoticz.Debug("Program information: " + str(self.startTime) + "-" + str(self.endTime) + " [" + str(self.perc_playingTime) + "%]")
                else:
                    self.tvPlaying = str(int(self.tvPlaying['dispNum'])) + ': ' + self.tvPlaying['title'] + ' - ' + self.tvPlaying['programTitle']
                UpdateDevice(1, 1, self.tvPlaying)
                self.tvSource = 10
                UpdateDevice(3, 1, str(self.tvSource))      # Set source device to TV
            else:                                           # No program info found
                if self.tvPlaying['title'] != '':
                    self.tvPlaying = self.tvPlaying['title']
                else:
                    self.tvPlaying = "Netflix"              # When TV plays apps, no title information (in this case '') is available, so assume Netflix is playing
                if "/MHL" in self.tvPlaying:                # Source contains /MHL, that can be removed
                    self.tvPlaying = self.tvPlaying.replace("/MHL", "")
                UpdateDevice(1, 1, self.tvPlaying)
                if "HDMI 1" in self.tvPlaying:
                    self.tvSource = 20
                    UpdateDevice(3, 1, str(self.tvSource))  # Set source device to HDMI1
                elif "HDMI 2" in self.tvPlaying:
                    self.tvSource = 30
                    UpdateDevice(3, 1, str(self.tvSource))  # Set source device to HDMI2
                elif "HDMI 3" in self.tvPlaying:
                    self.tvSource = 40
                    UpdateDevice(3, 1, str(self.tvSource))  # Set source device to HDMI3
                elif "HDMI 4" in self.tvPlaying:
                    self.tvSource = 50
                    UpdateDevice(3, 1, str(self.tvSource))  # Set source device to HDMI4
                elif "Netflix" in self.tvPlaying:
                    self.tvSource = 60
                    UpdateDevice(3, 1, str(self.tvSource))  # Set source device to Netflix
            
            # Get volume information of TV
            if Parameters["Mode3"] == "Volume":
                self.tvVolume = _tv.get_volume_info()
                self.tvVolume = self.tvVolume['volume']
                if self.tvVolume != None: UpdateDevice(2, 2, str(self.tvVolume))
                    
            # Update control and channel devices
            UpdateDevice(4, 1, str(self.tvControl))
            UpdateDevice(5, 1, str(self.tvChannel))
        
        return
"""

_plugin = BasePlugin()

def onStart():
    _plugin.onStart()

"""
def onCommand(Unit, Command, Level, Hue):
    _plugin.onCommand(Unit, Command, Level, Hue)

def onHeartbeat():
    _plugin.onHeartbeat()

# Update Device into database
def UpdateDevice(Unit, nValue, sValue, AlwaysUpdate=False):
    # Make sure that the Domoticz device still exists (they can be deleted) before updating it 
    if Unit in Devices:
        if ((Devices[Unit].nValue != nValue) or (Devices[Unit].sValue != sValue) or (AlwaysUpdate == True)):
            Devices[Unit].Update(nValue, str(sValue))
            Domoticz.Log("Update " + Devices[Unit].Name + ": " + str(nValue) + " - '" + str(sValue) + "'")
    return
"""
# Generic helper functions
def DumpConfigToLog():
    for x in Parameters:
        if Parameters[x] != "":
            Domoticz.Debug( "'" + x + "':'" + str(Parameters[x]) + "'")
    Domoticz.Debug("Device count: " + str(len(Devices)))
    for x in Devices:
        Domoticz.Debug("Device:           " + str(x) + " - " + str(Devices[x]))
        Domoticz.Debug("Internal ID:     '" + str(Devices[x].ID) + "'")
        Domoticz.Debug("External ID:     '" + str(Devices[x].DeviceID) + "'")
        Domoticz.Debug("Device Name:     '" + Devices[x].Name + "'")
        Domoticz.Debug("Device nValue:    " + str(Devices[x].nValue))
        Domoticz.Debug("Device sValue:   '" + Devices[x].sValue + "'")
        Domoticz.Debug("Device LastLevel: " + str(Devices[x].LastLevel))
    return
