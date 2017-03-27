LANGUAGE="EN"

###### DO NOT EDIT BELOW THIS LINE

VERSION_NUM = 2.041

show_video = (LANGUAGE == "EN")
show_instruct_text = (LANGUAGE == "SP")

# SYNC BOX REQUIRED
require_labjack=True

# ENCODING

encoding_orientation = 250
pre_encoding_delay = 500
pre_encoding_jitter = 250

encoding_orient_text = '+'

encoding_duration = 4000
post_encoding = 1000

# RETRIEVAL

cue_orientation = 250
pre_cue = 500
pre_cue_jitter = 250
cue_duration = 4000
post_cue = 1000

retrieval_start_text = '*******'
retrieval_orient_text = ''

# FORCED BREAK
forced_break_time = 10000
forced_break_message = "These were the pairs"

nPairs = 6
nTrials = 25
nSessions = 10

min_distract = 10000

countdownMovie = 'video_EN/countdown.mpg'

# practice wordlist
practice_wordList = 'txt_%s/word-pool_PRACTICE.txt' % LANGUAGE

# full wordpool
wp = 'txt_%s/RAM_wordpool.txt' % LANGUAGE
# wordpool without accents gets copied to
noAcc_wp = 'RAM_wordpool_noAcc.txt'

# Introductory movie
introMovie = 'video_%s/instructions.mpg' % LANGUAGE
introAudio = 'video_%s/instructions.wav' % LANGUAGE


# Instructions files
pre_practiceList = 'txt_%s/pre_practiceList.txt' % LANGUAGE
post_practiceList = 'txt_%s/post_practiceList.txt' % LANGUAGE
intro_file = 'txt_%s/intro.txt' % LANGUAGE
practice_instruct = 'txt_%s/practice_instruct.txt' % LANGUAGE

nStimLocs = 1

# Word font size (percentage of vertical screen)
wordHeight = .1 

startBeepFreq = 800
startBeepDur = 500
startBeepRiseFall = 100

# Math distractor options
doMathDistract = True
continuousDistract = False
MATH_numVars = 3
MATH_maxNum = 9
MATH_minNum = 1
MATH_maxProbs = 500
MATH_plusAndMinus = False
MATH_minDuration_Practice = 30000
MATH_minDuration = 20000
MATH_textSize = .1
MATH_correctBeepDur = 500
MATH_correctBeepFreq = 400
MATH_correctBeepRF = 50
MATH_correctSndFile = None
MATH_incorrectBeepDur = 500
MATH_incorrectBeepFreq = 200
MATH_incorrectBeepRF = 50
MATH_incorrectSndFile = None

fastConfig = False
if fastConfig:
    encoding_orientation = 25#0
    pre_encoding_delay = 50#0
    pre_encoding_jitter = 25#0

    encoding_orient_text = '+'

    encoding_duration = 40#00
    post_encoding = 10#00

    # RETRIEVAL

    cue_orientation = 25#0
    pre_cue = 50#0
    pre_cue_jitter = 25#0
    cue_duration = 40#00
    post_cue = 10#00
    
    doMathDistract = False
    MATH_minDuration = 20


