# RAM_FR configuration for NONSTIM SESSIONS ONLY.
# Other configuration in the main config file
# ALL SYSTEM2.0 CONFIGURATION OPTIONS
experiment = 'PAL3'
stim_type = 'CLOSED_STIM'
version = '3.0'
control_pc = True
heartbeat_interval = 1000

state_list = [
    'PRACTICE',
    'STIM ENCODING',
    'NON-STIM ENCODING',
    'RETRIEVAL',
    'DISTRACT',
    'INSTRUCT',
    'COUNTDOWN',
    'WAITING',
    'WORD',
    'ORIENT',
    'MIC TEST',
 ]

require_labjack = False

# THIS IS HOW THE REST OF THE PROGRAM KNOWS THIS IS A NONSTIM SESSION
do_stim = True

numSessions = 18

nBaselineTrials = 3
nStimTrials = 11
nControlTrials = 11
