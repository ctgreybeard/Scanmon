# -*- coding: ISO-8859-1 -*-
# Uniden Scanner utilities and programming access
"""
Uniden Scanner utilities and programming access

Module and class to communicate with a Uniden DMA scanner (BCD996XT, BCD396XT, etc.)
"""

import io, re, types, threading, time, logging
from serial import Serial
from glob import glob

# A useful function
def _lineno(lineidx): return '123456789'[lineidx:lineidx+1]

ERRORRESP = ('', 		# Null
			 'ERR', 	# Invalid command
			 'NG',		# Valid command, wrong mode
			 'FER',		# Framing error
			 'ORER')	# Overrun error

prematch = r'(?P<CMD>\w*)'	# Only need the first "word" on the line
prematchre = re.compile(prematch)

class Decode:
	'''
	Decode cmd results
	'''
	
	ISERRORKEY = 'iserror'
	ERRORCODEKEY = 'errorcode'
	
	# Some error codes and their descriptions
	NO_ERROR = 0
	ERR_PREMATCH = 1
	ERR_NOKEYWORDS = 2
	ERR_NOMATCH = 3
	ERR_RESPONSE = 4
	ERR_UNKNOWN_RESPONSE = 5
	
	ERRORMSG = {
		ERR_PREMATCH: 'Error in prematch',
		ERR_NOKEYWORDS: 'No keywords',
		ERR_NOMATCH: 'No match',
		ERR_RESPONSE: 'Error response from scanner',
		ERR_UNKNOWN_RESPONSE: 'Unknown response from scanner'
	}
	
	# Results processing functions
	def stspost(basedict):
		basedict['stspost'] = 'Done'	# Just for testing ...
	
	# Define decoding re's and methods for cmd results
	Decodes = {
		'STS': {	# STS is hard, it's variable in length
			'repre': r'STS,(?P<PREVAL>[01]{4,8}),',
			'recmd': lambda PREDICT: ''.join(('STS,(?P<DSP_FORM>[01]{4,8}),',
				''.join(
					map(lambda line: ''.join((
						'(?P<L',
						_lineno(line),
						'_CHAR>[^,]{,16}),(?P<L',
						_lineno(line),
						'_MODE>[^,]{,16}),')), 
					range(len(PREDICT['PREVAL'])))),
				r'(?P<SQL>\d?),(?P<MUT>\d?),(?P<BAT>\d?),(?P<RSV1>\d?),(?P<RSV2>\d?),(?P<WAT>\w{,4}),(?P<SIG_LVL>\d?),(?P<BK_COLOR>\w*),(?P<BK_DIMMER>\d)$')),
			'repost': stspost,	# Post processing routine
		},
		'ABP': {       # ABP is hard too, many possible BASE and SPACING pairs NOTE The code will need to split the request manualls
			'recmd': r'ABP,(?P<BASE_FREQ_0>[^,]*)(?:,(?P<SPACING_FREQ_0>[^,]*))?',
		},
		'ACC': {	# ACC
			'recmd': r'ACC,(?P<CHN_INDEX>[^,]*)',
		},
		'ACT': {	# ACT
			'recmd': r'ACT,(?P<INDEX>[^,]*)',
		},
		'AGC': {	# AGC
			'recmd': r'AGC,(?P<GRP_INDEX>[^,]*)',
		},
		'AGT': {	# AGT
			'recmd': r'AGT,(?P<GRP_INDEX>[^,]*)',
		},
		'AGV': {	# AGV
			'recmd': r'AGV,(?P<ANS>[^,]*)(?:,(?P<RSV1>[^,]*),(?P<A_RES>[^,]*),(?P<A_REF>[^,]*),(?P<A_GAIN>[^,]*),(?P<D_RES>[^,]*),(?P<D_GAIN>[^,]*))?',
		},
		'AST': {	# AST
			'recmd': r'AST,(?P<SITE_INDEX>[^,]*)',
		},
		'BAV': {	# BAV
			'recmd': r'BAV,(?P<ANS>[^,]*)',
		},
		'BBS': {	# BBS
			'recmd': r'BBS,(?P<LIMIT_L>[^,]*)(?:,(?P<LIMIT_H>[^,]*))?',
		},
		'BLT': {	# BLT
			'recmd': r'BLT,(?P<EVNT>[^,]*)(?:,(?P<COLOR>[^,]*),(?P<DIMMER>[^,]*))?',
		},
		'BSP': {	# BSP
			'recmd': r'BSP,(?P<FRQ>[^,]*)(?:,(?P<STP>[^,]*),(?P<SPN>[^,]*),(?P<MAX_HOLD>[^,]*))?',
		},
		'BSV': {	# BSV
			'recmd': r'BSV,(?P<BAT_SAVE>[^,]*)(?:,(?P<CHARGE_TIME>[^,]*))?',
		},
		'CBP': {	# CBP
			'recmd': r'CBP,(?P<MOT_TYPE>[^,]*)(?:,(?P<LOWER1>[^,]*),(?P<UPPER1>[^,]*),(?P<STEP1>[^,]*),(?P<OFFSET1>[^,]*),(?P<LOWER2>[^,]*),(?P<UPPER2>[^,]*),(?P<STEP2>[^,]*),(?P<OFFSET2>[^,]*),(?P<LOWER3>[^,]*),(?P<UPPER3>[^,]*),(?P<STEP3>[^,]*),(?P<OFFSET3>[^,]*),(?P<LOWER4>[^,]*),(?P<UPPER4>[^,]*),(?P<STEP4>[^,]*),(?P<OFFSET4>[^,]*),(?P<LOWER5>[^,]*),(?P<UPPER5>[^,]*),(?P<STEP5>[^,]*),(?P<OFFSET5>[^,]*),(?P<LOWER6>[^,]*),(?P<UPPER6>[^,]*),(?P<STEP6>[^,]*),(?P<OFFSET6>[^,]*))?',
		},
		'CIE': {	# CIE
			'recmd': r'CIE,(?P<ANS>[^,]*)',
		},
		'CIN': {	# CIN
			'recmd': r'CIN,(?P<NAME>[^,]*)(?:,(?P<FRQ>[^,]*),(?P<MOD>[^,]*),(?P<CTCSS(?:DCS>[^,]*),(?P<TLOCK>[^,]*),(?P<LOUT>[^,]*),(?P<PRI>[^,]*),(?P<ATT>[^,]*),(?P<ALT>[^,]*),(?P<ALTL>[^,]*),(?P<REV_INDEX>[^,]*),(?P<FWD_INDEX>[^,]*),(?P<SYS_INDEX>[^,]*),(?P<GRP_INDEX>[^,]*),(?P<RSV1>[^,]*),(?P<AUDIO_TYPE>[^,]*),(?P<P25NAC>[^,]*),(?P<NUMBER_TAG>[^,]*),(?P<ALT_COLOR>[^,]*),(?P<ALT_PATTERN>[^,]*),(?P<VOL_OFFSET>[^,]*))?',
		},
		'CLA': {	# CLA
			'recmd': r'CLA,(?P<INDEX>[^,]*)',
		},
		'CLC': {	# CLC
			'recmd': r'CLC,(?P<CC_MODE>[^,]*)(?:,(?P<CC_OVERRIDE>[^,]*),(?P<RSV1>[^,]*),(?P<ALTB>[^,]*),(?P<ALTL>[^,]*),(?P<ALTP>[^,]*),(?P<CC_BAND>[^,]*),(?P<LOUT>[^,]*),(?P<HLD>[^,]*),(?P<QUICK_KEY>[^,]*),(?P<NUMBER_TAG>[^,]*),(?P<ALT_COLOR>[^,]*),(?P<ALT_PATTERN>[^,]*))?',
		},
		'CLR': {	# CLR
			'recmd': r'CLR,(?P<ANS>[^,]*)',
		},
		'CNT': {	# CNT
			'recmd': r'CNT,(?P<CONTRAST>[^,]*)',
		},
		'COM': {	# COM
			'recmd': r'COM,(?P<BAUDRATE>[^,]*)(?:,(?P<RSV1>[^,]*))?',
		},
		'CSC': {	# CSC
			'recmd': r'CSC,(?P<RSSI>[^,]*)(?:,(?P<FRQ>[^,]*),(?P<SQL>[^,]*))?',
		},
		'CSG': {	# CSG
			'recmd': r'CSG,(?P<ANS>[^,]*)',
		},
		'CSP': {	# CSP
			'recmd': r'CSP,(?P<NAME>[^,]*)(?:,(?P<LIMIT_L>[^,]*),(?P<LIMIT_H>[^,]*),(?P<STP>[^,]*),(?P<MOD>[^,]*),(?P<ATT>[^,]*),(?P<DLY>[^,]*),(?P<RSV1>[^,]*),(?P<HLD>[^,]*),(?P<LOUT>[^,]*),(?P<C-CH>[^,]*),(?P<RSV2>[^,]*),(?P<RSV3>[^,]*),(?P<QUICK_KEY>[^,]*),(?P<START_KEY>[^,]*),(?P<RSV4>[^,]*),(?P<NUMBER_TAG>[^,]*),(?P<AGC_ANALOG>[^,]*),(?P<AGC_DIGITAL>[^,]*),(?P<P25WAITING>[^,]*))?',
		},
		'CSY': {	# CSY
			'recmd': r'CSY,(?P<SYS_INDEX>[^,]*)',
		},
		'DBC': {	# DBC
			'recmd': r'DBC,(?P<STEP>[^,]*)(?:,(?P<MOD>[^,]*))?',
		},
		'DCH': {	# DCH
			'recmd': r'DCH,(?P<ANS>[^,]*)',
		},
		'DGR': {	# DGR
			'recmd': r'DGR,(?P<ANS>[^,]*)',
		},
		'DLA': {	# DLA
			'recmd': r'DLA,(?P<ANS>[^,]*)',
		},
		'DSY': {	# DSY
			'recmd': r'DSY,(?P<ANS>[^,]*)',
		},
		'EPG': {	# EPG
			'recmd': r'EPG,(?P<ANS>[^,]*)',
		},
		'FWD': {	# FWD
			'recmd': r'FWD,(?P<INDEX>[^,]*)',
		},
		'GDO': {	# GDO
			'recmd': r'GDO,(?P<DISP_MODE>[^,]*)(?:,(?P<UNIT>[^,]*),(?P<TIME_FORMAT>[^,]*),(?P<TIME_ZONE>[^,]*),(?P<POS_FORMAT>[^,]*))?',
		},
		'GID': {	# GID
			'recmd': r'GID,(?P<SITE_TYPE>[^,]*)(?:,(?P<TGID>[^,]*),(?P<ID_SRCH_MODE>[^,]*),(?P<NAME1>[^,]*),(?P<NAME2>[^,]*),(?P<NAME3>[^,]*))?',
		},
		'GIE': {	# GIE
			'recmd': r'GIE,(?P<FRQ>[^,]*)',
		},
		'GIN': {	# GIN
			'recmd': r'GIN,(?P<GRP_TYPE>[^,]*)(?:,(?P<NAME>[^,]*),(?P<QUICK_KEY>[^,]*),(?P<LOUT>[^,]*),(?P<REV_INDEX>[^,]*),(?P<FWD_INDEX>[^,]*),(?P<SYS_INDEX>[^,]*),(?P<CHN_HEAD>[^,]*),(?P<CHN_TAIL>[^,]*),(?P<SEQ_NO>[^,]*),(?P<LATITUDE>[^,]*),(?P<LONGITUDE>[^,]*),(?P<RANGE>[^,]*),(?P<GPSENABLE>[^,]*))?',
		},
		'GLF': {	# GLF
			'recmd': r'GLF,(?P<FRQ>[^,]*)',
		},
		'GLG': {	# GLG
			'recmd': r'GLG,(?P<FRQ_TGID>[^,]*),(?P<MOD>[^,]*),(?P<ATT>[^,]*),(?P<CTCSS_DCS>[^,]*),(?P<NAME1>[^,]*),(?P<NAME2>[^,]*),(?P<NAME3>[^,]*),(?P<SQL>[^,]*),(?P<MUT>[^,]*),(?P<SYS_TAG>[^,]*),(?P<CHAN_TAG>[^,]*),(?P<P25NAC>[^,]*)',
		},
		'GLI': {	# GLI
			'recmd': r'GLI,(?P<TGID>[^,]*)',
		},
		'JNT': {	# JNT
			'recmd': r'JNT,(?P<ANS>[^,]*)',
		},
		'JPM': {	# JPM
			'recmd': r'JPM,(?P<ANS>[^,]*)',
		},
		'KBP': {	# KBP
			'recmd': r'KBP,(?P<LEVEL>[^,]*)(?:,(?P<LOCK>[^,]*),(?P<SAFE>[^,]*))?',
		},
		'KEY': {	# KEY
			'recmd': r'KEY,(?P<ANS>[^,]*)',
		},
		'LIH': {	# LIH
			'recmd': r'LIH,(?P<INDEX>[^,]*)',
		},
		'LIN': {	# LIN
			'recmd': r'LIN,(?P<LAS_TYPE>[^,]*)(?:,(?P<NAME>[^,]*),(?P<LOUT>[^,]*),(?P<ALT>[^,]*),(?P<ALTL>[^,]*),(?P<REV_INDEX>[^,]*),(?P<FWD_INDEX>[^,]*),(?P<SEQ_NO>[^,]*),(?P<LATITUDE>[^,]*),(?P<LONGITUDE>[^,]*),(?P<RANGE>[^,]*),(?P<SPEED>[^,]*),(?P<DIR>[^,]*),(?P<ALT_COLOR>[^,]*),(?P<ALT_PATTERN>[^,]*))?',
		},
		'LIT': {	# LIT
			'recmd': r'LIT,(?P<INDEX>[^,]*)',
		},
		'LOF': {	# LOF
			'recmd': r'LOF,(?P<ANS>[^,]*)',
		},
		'LOI': {	# LOI
			'recmd': r'LOI,(?P<SYS_INDEX>[^,]*)(?:,(?P<TGID>[^,]*))?',
		},
		'MCP': {	# MCP
			'recmd': r'MCP,(?P<LOWER1>[^,]*)(?:,(?P<UPPER1>[^,]*),(?P<STEP1>[^,]*),(?P<OFFSET1>[^,]*),(?P<LOWER2>[^,]*),(?P<UPPER2>[^,]*),(?P<STEP2>[^,]*),(?P<OFFSET2>[^,]*),(?P<LOWER3>[^,]*),(?P<UPPER3>[^,]*),(?P<STEP3>[^,]*),(?P<OFFSET3>[^,]*),(?P<LOWER4>[^,]*),(?P<UPPER4>[^,]*),(?P<STEP4>[^,]*),(?P<OFFSET4>[^,]*),(?P<LOWER5>[^,]*),(?P<UPPER5>[^,]*),(?P<STEP5>[^,]*),(?P<OFFSET5>[^,]*),(?P<LOWER6>[^,]*),(?P<UPPER6>[^,]*),(?P<STEP6>[^,]*),(?P<OFFSET6>[^,]*))?',
		},
		'MDL': {	# MDL
			'recmd': r'MDL,(?P<MODEL>[^,]*)',
		},
		'MEM': {	# MEM
			'recmd': r'MEM,(?P<MEMORY_USED>[^,]*),(?P<SYS>[^,]*),(?P<SITE>[^,]*),(?P<CHN>[^,]*),(?P<LOC>[^,]*)',
		},
		'MNU': {	# MNU
			'recmd': r'MNU,(?P<ANS>[^,]*)',
		},
		'OMS': {	# OMS
			'recmd': r'OMS,(?P<L1_CHAR>[^,]*)(?:,(?P<L2_CHAR>[^,]*),(?P<L3_CHAR>[^,]*),(?P<L4_CHAR>[^,]*))?',
		},
		'P25': {	# P25
			'recmd': r'P25,(?P<RSV1>[^,]*),(?P<RSV2>[^,]*),(?P<ERR_RATE>[^,]*)',
		},
		'POF': {	# POF
			'recmd': r'POF,(?P<ANS>[^,]*)',
		},
		'PRG': {	# PRG
			'recmd': r'PRG,(?P<ANS>[^,]*)',
		},
		'PRI': {	# PRI
			'recmd': r'PRI,(?P<PRI_MODE>[^,]*)(?:,(?P<MAX_CHAN>[^,]*),(?P<INTERVAL>[^,]*))?',
		},
		'PWR': {	# PWR
			'recmd': r'PWR,(?P<RSSI>[^,]*),(?P<FRQ>[^,]*)',
		},
		'QGL': {	# QGL
			'recmd': r'QGL,(?P<STATUS>[^,]*)',
		},
		'QSC': {	# QSC
			'recmd': r'QSC,(?P<RSSI>[^,]*)(?:,(?P<FRQ>[^,]*),(?P<SQL>[^,]*))?',
		},
		'QSH': {	# QSH
			'recmd': r'QSH,(?P<ANS>[^,]*)',
		},
		'QSL': {	# QSL
			'recmd': r'QSL,(?P<PAGE0>[^,]*)(?:,(?P<PAGE1>[^,]*),(?P<PAGE2>[^,]*),(?P<PAGE3>[^,]*),(?P<PAGE4>[^,]*),(?P<PAGE5>[^,]*),(?P<PAGE6>[^,]*),(?P<PAGE7>[^,]*),(?P<PAGE8>[^,]*),(?P<PAGE9>[^,]*))?',
		},
		'REV': {	# REV
			'recmd': r'REV,(?P<INDEX>[^,]*)',
		},
		'RIE': {	# RIE
			'recmd': r'RIE,(?P<ANS>[^,]*)',
		},
		'RM': {	# RMB
			'recmd': r'RMB,(?P<FREE>[^,]*)',
		},
		'SCN': {	# SCN
			'recmd': r'SCN,(?P<DISP_MODE>[^,]*)(?:,(?P<RSV1>[^,]*),(?P<CH_LOG>[^,]*),(?P<G_ATT>[^,]*),(?P<RSV2>[^,]*),(?P<P25_LPF>[^,]*),(?P<RSV3>[^,]*),(?P<RSV4>[^,]*),(?P<RSV5>[^,]*),(?P<RSV6>[^,]*),(?P<RSV7>[^,]*),(?P<RSV8>[^,]*),(?P<RSV9>[^,]*),(?P<RSV10>[^,]*),(?P<RSV11>[^,]*),(?P<RSV12>[^,]*),(?P<RSV13>[^,]*),(?P<RSV14>[^,]*),(?P<RSV15>[^,]*),(?P<RSV16>[^,]*),(?P<RSV17>[^,]*))?',
		},
		'SCO': {	# SCO
			'recmd': r'SCO,(?P<ANS>[^,]*)(?:,(?P<MOD>[^,]*),(?P<ATT>[^,]*),(?P<DLY>[^,]*),(?P<RSV1>[^,]*),(?P<CODE_SRCH>[^,]*),(?P<BSC>[^,]*),(?P<REP>[^,]*),(?P<RSV2>[^,]*),(?P<RSV3>[^,]*),(?P<MAX_STORE>[^,]*),(?P<RSV4>[^,]*),(?P<AGC_ANALOG>[^,]*),(?P<AGC_DIGITAL>[^,]*),(?P<P25WAITING>[^,]*))?',
		},
		'SCT': {	# SCT
			'recmd': r'SCT,(?P<COUNT>[^,]*)',
		},
		'SGP': {	# SGP
			'recmd': r'SGP,(?P<NAME>[^,]*)(?:,(?P<FIPS1>[^,]*),(?P<FIPS2>[^,]*),(?P<FIPS3>[^,]*),(?P<FIPS4>[^,]*),(?P<FIPS5>[^,]*),(?P<FIPS6>[^,]*),(?P<FIPS7>[^,]*),(?P<FIPS8>[^,]*))?',
		},
		'SHK': {	# SHK
			'recmd': r'SHK,(?P<SRCH_KEY_1>[^,]*)(?:,(?P<SRCH_KEY_2>[^,]*),(?P<SRCH_KEY_3>[^,]*),(?P<RSV1>[^,]*),(?P<RSV2>[^,]*),(?P<RSV3>[^,]*))?',
		},
		'SIF': {	# SIF
			'recmd': r'SIF,(?P<RSV1>[^,]*)(?:,(?P<NAME>[^,]*),(?P<QUICK_KEY>[^,]*),(?P<HLD>[^,]*),(?P<LOUT>[^,]*),(?P<MOD>[^,]*),(?P<ATT>[^,]*),(?P<C_CH>[^,]*),(?P<RSV2>[^,]*),(?P<RSV3>[^,]*),(?P<REV_INDEX>[^,]*),(?P<FWD_INDEX>[^,]*),(?P<SYS_INDEX>[^,]*),(?P<CHN_HEAD>[^,]*),(?P<CHN_TAIL>[^,]*),(?P<SEQ_NO>[^,]*),(?P<START_KEY>[^,]*),(?P<LATITUDE>[^,]*),(?P<LONGITUDE>[^,]*),(?P<RANGE>[^,]*),(?P<GPS_ENABLE>[^,]*),(?P<RSV4>[^,]*),(?P<MOT_TYPE>[^,]*),(?P<EDACS_TYPE>[^,]*),(?P<P25WAITING>[^,]*),(?P<RSV5>[^,]*))?',
		},
		'SIH': {	# SIH
			'recmd': r'SIH,(?P<SYS_INDEX>[^,]*)',
		},
		'SIN': {	# SIN
			'recmd': r'SIN,(?P<SYS_TYPE>[^,]*)(?:,(?P<NAME>[^,]*),(?P<QUICK_KEY>[^,]*),(?P<HLD>[^,]*),(?P<LOUT>[^,]*),(?P<DLY>[^,]*),(?P<RSV1>[^,]*),(?P<RSV2>[^,]*),(?P<RSV3>[^,]*),(?P<RSV4>[^,]*),(?P<RSV5>[^,]*),(?P<REV_INDEX>[^,]*),(?P<FWD_INDEX>[^,]*),(?P<CHN_GRP_HEAD>[^,]*),(?P<CHN_GRP_TAIL>[^,]*),(?P<SEQ_NO>[^,]*),(?P<START_KEY>[^,]*),(?P<RSV6>[^,]*),(?P<RSV7>[^,]*),(?P<RSV8>[^,]*),(?P<RSV9>[^,]*),(?P<RSV10>[^,]*),(?P<NUMBER_TAG>[^,]*),(?P<AGC_ANALOG>[^,]*),(?P<AGC_DIGITAL>[^,]*),(?P<P25WAITING>[^,]*),(?P<PROTECT>[^,]*),(?P<RSV11>[^,]*))?',
		},
		'SIT': {	# SIT
			'recmd': r'SIT,(?P<SYS_INDEX>[^,]*)',
		},
		'SLI': {	# SLI
			'recmd': r'SLI,(?P<TGID>[^,]*)',
		},
		'SQL': {	# SQL
			'recmd': r'SQL,(?P<LEVEL>[^,]*)',
		},
		'SSP': {	# SSP
			'recmd': r'SSP,(?P<SRCH_INDEX>[^,]*)(?:,(?P<DLY>[^,]*),(?P<ATT>[^,]*),(?P<HLD>[^,]*),(?P<LOUT>[^,]*),(?P<QUICK_KEY>[^,]*),(?P<START_KEY>[^,]*),(?P<RSV1>[^,]*),(?P<NUMBER_TAG>[^,]*),(?P<AGC_ANALOG>[^,]*),(?P<AGC_DIGITAL>[^,]*),(?P<P25WAITING>[^,]*))?',
		},
		'TFQ': {	# TFQ
			'recmd': r'TFQ,(?P<FRQ>[^,]*)(?:,(?P<LCN>[^,]*),(?P<LOUT>[^,]*),(?P<REV_INDEX>[^,]*),(?P<FWD_INDEX>[^,]*),(?P<SYS_INDEX>[^,]*),(?P<GRP_INDEX>[^,]*),(?P<RSV1>[^,]*),(?P<NUMBER_TAG>[^,]*),(?P<VOL_OFFSET>[^,]*),(?P<RSV2>[^,]*))?',
		},
		'TIN': {	# TIN
			'recmd': r'TIN,(?P<NAME>[^,]*)(?:,(?P<TGID>[^,]*),(?P<LOUT>[^,]*),(?P<PRI>[^,]*),(?P<ALT>[^,]*),(?P<ALTL>[^,]*),(?P<REV_INDEX>[^,]*),(?P<FWD_INDEX>[^,]*),(?P<SYS_INDEX>[^,]*),(?P<GRP_INDEX>[^,]*),(?P<RSV1>[^,]*),(?P<AUDIO_TYPE>[^,]*),(?P<NUMBER_TAG>[^,]*),(?P<ALT_COLOR>[^,]*),(?P<ALT_PATTERN>[^,]*),(?P<VOL_OFFSET>[^,]*))?',
		},
		'TON': {	# TON
			'recmd': r'TON,(?P<INDEX>[^,]*)(?:,(?P<NAME>[^,]*),(?P<FRQ>[^,]*),(?P<MOD>[^,]*),(?P<ATT>[^,]*),(?P<DLY>[^,]*),(?P<ALT>[^,]*),(?P<ALTL>[^,]*),(?P<TONE_A>[^,]*),(?P<RSV1>[^,]*),(?P<TONE_B>[^,]*),(?P<RSV2>[^,]*),(?P<RSV3>[^,]*),(?P<RSV4>[^,]*),(?P<ALT_COLOR>[^,]*),(?P<ALT_PATTERN>[^,]*),(?P<AGC_ANALOG>[^,]*),(?P<RSV5>[^,]*),(?P<RSV6>[^,]*))?',
		},
		'TRN': {	# TRN
			'recmd': r'TRN,(?P<ID_SEARCH>[^,]*)(?:,(?P<S_BIT>[^,]*),(?P<END_CODE>[^,]*),(?P<AFS>[^,]*),(?P<RSV1>[^,]*),(?P<RSV2>[^,]*),(?P<EMG>[^,]*),(?P<EMGL>[^,]*),(?P<FMAP>[^,]*),(?P<CTM_FMAP>[^,]*),(?P<RSV3>[^,]*),(?P<RSV4>[^,]*),(?P<RSV5>[^,]*),(?P<RSV6>[^,]*),(?P<RSV7>[^,]*),(?P<RSV8>[^,]*),(?P<RSV9>[^,]*),(?P<RSV10>[^,]*),(?P<RSV11>[^,]*),(?P<RSV12>[^,]*),(?P<TGID_GRP_HEAD>[^,]*),(?P<TGID_GRP_TAIL>[^,]*),(?P<ID_LOUT_GRP_HEAD>[^,]*),(?P<ID_LOUT_GRP_TAIL>[^,]*),(?P<MOT_ID>[^,]*),(?P<EMG_COLOR>[^,]*),(?P<EMG_PATTERN>[^,]*),(?P<P25NAC>[^,]*),(?P<PRI_ID_SCAN>[^,]*))?',
		},
		'ULF': {	# ULF
			'recmd': r'ULF,(?P<FRQ>[^,]*)',
		},
		'ULI': {	# ULI
			'recmd': r'ULI,(?P<ANS>[^,]*)',
		},
		'VER': {	# VER
			'recmd': r'VER,(?P<VERSION>[^,]*)',
		},
		'VOL': {	# VOL
			'recmd': r'VOL,(?P<LEVEL>[^,]*)',
		},
		'WIN': {	# WIN
			'recmd': r'WIN,(?P<ANS>[^,]*)',
		},
		'WXS': {	# WXS
			'recmd': r'WXS,(?P<DLY>[^,]*)(?:,(?P<ATT>[^,]*),(?P<ALT_PRI>[^,]*),(?P<RSV1>[^,]*),(?P<AGC_ANALOG>[^,]*),(?P<RSV2>[^,]*))?',
		},
	}

	def domatch(tomatch):

		global prematchre, ERRORRESP
	
		def doIt(target, request, basedict, addgroups):

			regex = re.compile(request, flags = 0)
			rematch = regex.match(target)
			
			if rematch is not None:
				basedict.update(rematch.groupdict(default=''))
				if addgroups:
					basedict.update({'groups': rematch.groups(default='')})
			else:
				 basedict.update({Decode.ISERRORKEY: True, Decode.ERRORCODEKEY: Decode.ERR_NOMATCH})
	
		def runIt(target, request, basedict, addgroups = False):
			nonlocal doIt
		
			if isinstance(request, types.FunctionType):
				doIt(target, request(basedict), basedict, addgroups)
		
			elif isinstance(request, str):
				doIt(target, request, basedict, addgroups)
		
			else:
				raise ValueError("Invalid decode type")
	
		dec = Decode()
	
		matchresult = {	# Set some default results
			'CMD': '', 
			'iserror': False, 
			'isOK': False,
			'errorcode': Decode.NO_ERROR,
			'response': tomatch,
		}

		prematch = prematchre.match(tomatch)
		if prematch is None: 
			Scanner.logger.error('Prematch failed for: %s', tomatch)
			matchresult.update({Decode.ISERRORKEY: True, Decode.ERRORCODEKEY: Decode.ERR_PREMATCH})
		
		else:	# Prematch OK, try the main event
			# Update the results
			matchresult.update(prematch.groupdict())
	
			resp = prematch.group(1)	# What did we find?
			Scanner.logger.debug('Prematch found: %s', str(resp))
	
			if resp in ERRORRESP:		# Error response, can't go further
				Scanner.logger.error('Scanner error response: "%s"', tomatch)
				matchresult.update({'CMD': resp, Decode.ISERRORKEY: True, Decode.ERRORCODEKEY: Decode.ERR_RESPONSE})
		
			elif resp in dec.Decodes:
				matchresult['CMD'] = resp
				# OK, we know what to do ... I hope
		
				# First, run the prematch if it exists
				if 'repre' in dec.Decodes[resp]:
					runIt(tomatch, dec.Decodes[resp]['repre'], matchresult)
			
				# So far, so good. Now run the main event
				if 'recmd' in dec.Decodes[resp]:	# Should usually be there
					runIt(tomatch, dec.Decodes[resp]['recmd'], matchresult, addgroups = True)
					if matchresult.get('groups', [''])[0] == 'OK' \
						and len(matchresult['groups']) == 1: 
						matchresult['isOK'] = True
				
				if 'repost' in dec.Decodes[resp]:	# Post processing
					dec.Decodes[resp]['repost'](matchresult)
		
			else:
				Scanner.logger.error('Scanner unknown response: %s', tomatch)
				matchresult.update({Decode.ISERRORKEY: True, Decode.ERRORCODEKEY: Decode.ERR_UNKNOWN_RESPONSE})
		
		return matchresult

class Scanner(Serial):
	"""
	Scanner class - Handles opening IO to the scanner and command write with response read.
	"""
	
	COOKED = 0
	RAW = 1
	DECODED = 2
	
	COMRATES = (4800, 9600, 19200, 38400, 57600, 115200) # Possible COM port speeds
	
	ServiceModes = dict((('air', '6'), ('cb', '7'), ('fm', '11'), ('frs', '8'), 
		('ham', '3'), ('marine', '4'), ('military', '15'), ('news', '2'), 
		('publicsafety', '1'), ('racing', '9'), ('railroad', '5'), ('special', '12')))

	def __init__(self, port = None, baudrate = 0, timeout = 0.25, logname = __name__):
		'''
		Initialize the underlying serial port and provide the wrapper
		'''
		
		Serial.__init__(self, port = port, baudrate = baudrate, timeout = timeout)
		self._sior = io.BufferedReader(self)
		self._siow = io.BufferedWriter(self)

		self.MDL = '?'
		self.VER = '?'
		Scanner.logger = logging.getLogger(logname)

		if port is not None:
			self.logopen()
	
		self._sio_lock = threading.RLock()

	def logopen(self):
		if self.isOpen():
			self.MDL = self.cmd('MDL').split(',')[-1]
			self.VER = self.cmd('VER').split(',')[-1]
			Scanner.logger.info('Scanner model: %s, version: %s', self.MDL, self.VER)
		else:
			Scanner.logger.warning('Scanner (port: %s, baudrate: %d) should be open but is not',
				self.port, self.baudrate)
		
	def discover(self):
		'''
		Discover the Scanner port
		
		Currently only the PL2303 is acceptable. This will expand later in development
		'''
		
		if self.port is None:	# Look for the port
			devs_prefix = ['/dev/cu.PL2303*',] # Just PL2303 devices for now
			pdevs = [glob(pref) for pref in devs_prefix]
			# Use the first match
			for pdev1 in pdevs:
				if len(pdev1) > 0:
					self.port = pdev1[0]
					break
				
		if self.port is None:	# Still bad ... not good
			Scanner.logger.error('Unable to discover scanner using: %s', str(devs_prefix))
			return False
		else:
			Scanner.logger.info('Found device on: %s', self.port)
		
		self.baudrate = 19200	# Temporary default
		
		self.open()
		
		self.logopen()
		
		return self.isOpen()

	def _readresp(self):
		b = bytes()
		gotline = False

		def timeout():
			nonlocal gotline
			
			self.logger.warning('Readresp Timeout, got "%s" so far', str(b))
			gotline = True
			
		to = threading.Timer(2, timeout)
		to.start()
		try:
			while not gotline:
				c = self._sior.read(1)

				if len(c) > 0:
					b += c
					if c[-1] == 13:		# ord(b'\r') == 13
						gotline = True
		except:
			print('Oops ... got "{}" so far ...'.format(b))
		
		to.cancel()
		return b
		
	def cmd(self, cmd_string, cooked = COOKED):
		'''
		Send a command and return the response
		
		The line ending '\r' is automatically added and removed
		'''
		with self._sio_lock:	# Ensure we don't do two write/reads at the same time
			self._siow.write((cmd_string + '\r').encode('ISO-8859-1'))
			self._siow.flush()
		
			rawresp = self._readresp()
			if len(rawresp) == 0:	# Hmmm, we should never get a NULL response ... try once more
				Scanner.logger.warning('Scanner returned null response, retrying')
				rawresp = self._readresp()
				Scanner.logger.warning('Received: "%s"', str(rawresp))
		
			if rawresp.endswith(b'\r'): rawresp = rawresp[:-1] # Strip the '\r'
		
			# If it's not RAW, we cook it
			if cooked != Scanner.RAW: resp = self.cookIt(rawresp)
			else: resp = rawresp
		
			# Would you like Decoded with that?
			if cooked == Scanner.DECODED: 
				resp = self.decodeIt(resp)
				resp['rawresponse'] = rawresp
		
		return resp
	
	# Drain is only used when there may be a problem. It is supposed to resynchronize the streams
	# This takes a while so don't use it lightly
	def drain(self):
		with self._sio_lock: # Grab the interface
			Scanner.logger.warning('Draining...')
			self._siow.flush()		# Flush any output
			self._sior.detach()		# Dump the current BufferedReader
			self._siow.detach()		# And the current BufferedWriter
			self._sior = io.BufferedReader(self)
			self._siow = io.BufferedWriter(self)
			return
			
		
	def cookIt(self, resp):
		'''
		Create an ascii string from the bytes input
		Any non-ASCII chars (ord >127) are replaced with '?'
		'''
		# print('Cooked')
		if not isinstance(resp, bytes):
			Scanner.logger.critical('CookIt(): I can only cook bytes!')
			raise TypeError('Scanner.CookIt(): I can only cook bytes!')
		
		return bytes([c if c < 127 else ord('?') for c in resp]).decode('ASCII')
		
	def decodeIt(self, resp):
		'''
		Decode a cooked response into the corresponding structure
		'''
		# print('Decoded')
		return Decode.domatch(resp)