# RAM_FR configuration for NONSTIM SESSIONS ONLY.
# Other configuration in the main config file
EXPERIMENT_NAME='PAL0'
# ALL SYSTEM2.0 CONFIGURATION OPTIONS

sys2 = {
        'EXPERIMENT_NAME'  : 'PAL0',
        'VERSION_NUM'      : '2.04',
        'control_pc'       : 0,  # Will be incremented later for other control pc versions.  Set to 0 to turn off control pc processing
        }

require_labjack = False

# THIS IS HOW THE REST OF THE PROGRAM KNOWS THIS IS A NONSTIM SESSION
do_stim = False

numSessions = 18

nBaselineTrials = 0
nStimTrials = 0
nControlTrials = 25
