# -*- coding: ISO-8859-1 -*-
# Uniden Scanner utilities and programming access
"""
Uniden Scanner utilities and programming access

Module and class to communicate with a Uniden DMA scanner (BCD996XT, BCD396XT, etc.)
"""

import io, re, types
from serial import Serial
from glob import glob

# A useful function
def _lineno(lineidx): return b'123456789'[lineidx:lineidx+1]
	
ERRORRESP = (b'', 		# Null
			 b'ERR', 	# Invalid command
			 b'NG',		# Valid command, wrong mode
			 b'FER',	# Framing error
			 b'ORER')	# Overrun error
			 

prematch = rb'(?P<CMD>\w*)'	# Only need the first "word" on the line
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
		b'STS': {	# STS is hard, it's variable in length
			'repre': rb'STS,(?P<PREVAL>[01]{4,8}),',
			'recmd': lambda PREDICT: b''.join((b'STS,(?P<DSP_FORM>[01]{4,8}),',
				b''.join(
					map(lambda line: b''.join((
						b'(?P<L',
						_lineno(line),
						b'_CHAR>[^,]{,16}),(?P<L',
						_lineno(line),
						b'_MODE>[^,]{,16}),')), 
					range(len(PREDICT['PREVAL'])))),
				rb'(?P<SQL>\d?),(?P<MUT>\d?),(?P<BAT>\d?),(?P<RSV1>\d?),(?P<RSV2>\d?),(?P<WAT>\w{,4}),(?P<SIG_LVL>\d?),(?P<BK_COLOR>\w*),(?P<BK_DIMMER>\d)$')),
			'repost': stspost,	# Post processing routine
		},
		b'ABP': {       # ABP is hard too, many possible BASE and SPACING pairs NOTE The code will need to split the request manualls
			'recmd': rb'ABP,(?P<BASE_FREQ_0>[^,]*),(?P<SPACING_FREQ_0>[^,]*)',
		},
		
		b'ACC': {	# ACC
			'recmd': rb'ACC,(?P<CHN_INDEX>[^,]*)',
		},


		b'ACT': {	# ACT
			'recmd': rb'ACT,(?P<INDEX>[^,]*)',
		},


		b'AGC': {	# AGC
			'recmd': rb'AGC,(?P<GRP_INDEX>[^,]*)',
		},


		b'AGT': {	# AGT
			'recmd': rb'AGT,(?P<GRP_INDEX>[^,]*)',
		},


		b'AGV': {	# AGV
			'recmd': rb'AGV,(?P<ANS>[^,]*)(:?,(?P<RSV1>[^,]*),(?P<A_RES>[^,]*),(?P<A_REF>[^,]*),(?P<A_GAIN>[^,]*),(?P<D_RES>[^,]*),(?P<D_GAIN>[^,]*))?',
		},


		b'AST': {	# AST
			'recmd': rb'AST,(?P<SITE_INDEX>[^,]*)',
		},


		b'BAV': {	# BAV
			'recmd': rb'BAV,(?P<ANS>[^,]*)',
		},


		b'BBS': {	# BBS
			'recmd': rb'BBS,(?P<LIMIT_L>[^,]*)(:?,(?P<LIMIT_H>[^,]*))?',
		},


		b'BLT': {	# BLT
			'recmd': rb'BLT,(?P<EVNT>[^,]*)(:?,(?P<COLOR>[^,]*),(?P<DIMMER>[^,]*))?',
		},


		b'BSP': {	# BSP
			'recmd': rb'BSP,(?P<FRQ>[^,]*)(:?,(?P<STP>[^,]*),(?P<SPN>[^,]*),(?P<MAX_HOLD>[^,]*))?',
		},


		b'BSV': {	# BSV
			'recmd': rb'BSV,(?P<BAT_SAVE>[^,]*)(:?,(?P<CHARGE_TIME>[^,]*))?',
		},


		b'CBP': {	# CBP
			'recmd': rb'CBP,(?P<MOT_TYPE>[^,]*)(:?,(?P<LOWER1>[^,]*),(?P<UPPER1>[^,]*),(?P<STEP1>[^,]*),(?P<OFFSET1>[^,]*),(?P<LOWER2>[^,]*),(?P<UPPER2>[^,]*),(?P<STEP2>[^,]*),(?P<OFFSET2>[^,]*),(?P<LOWER3>[^,]*),(?P<UPPER3>[^,]*),(?P<STEP3>[^,]*),(?P<OFFSET3>[^,]*),(?P<LOWER4>[^,]*),(?P<UPPER4>[^,]*),(?P<STEP4>[^,]*),(?P<OFFSET4>[^,]*),(?P<LOWER5>[^,]*),(?P<UPPER5>[^,]*),(?P<STEP5>[^,]*),(?P<OFFSET5>[^,]*),(?P<LOWER6>[^,]*),(?P<UPPER6>[^,]*),(?P<STEP6>[^,]*),(?P<OFFSET6>[^,]*))?',
		},


		b'CIE': {	# CIE
			'recmd': rb'CIE,(?P<ANS>[^,]*)',
		},


		b'CIN': {	# CIN
			'recmd': rb'CIN,(?P<NAME>[^,]*)(:?,(?P<FRQ>[^,]*),(?P<MOD>[^,]*),(?P<CTCSS(:?DCS>[^,]*),(?P<TLOCK>[^,]*),(?P<LOUT>[^,]*),(?P<PRI>[^,]*),(?P<ATT>[^,]*),(?P<ALT>[^,]*),(?P<ALTL>[^,]*),(?P<REV_INDEX>[^,]*),(?P<FWD_INDEX>[^,]*),(?P<SYS_INDEX>[^,]*),(?P<GRP_INDEX>[^,]*),(?P<RSV1>[^,]*),(?P<AUDIO_TYPE>[^,]*),(?P<P25NAC>[^,]*),(?P<NUMBER_TAG>[^,]*),(?P<ALT_COLOR>[^,]*),(?P<ALT_PATTERN>[^,]*),(?P<VOL_OFFSET>[^,]*))?',
		},


		b'CLA': {	# CLA
			'recmd': rb'CLA,(?P<INDEX>[^,]*)',
		},


		b'CLC': {	# CLC
			'recmd': rb'CLC,(?P<CC_MODE>[^,]*)(:?,(?P<CC_OVERRIDE>[^,]*),(?P<RSV1>[^,]*),(?P<ALTB>[^,]*),(?P<ALTL>[^,]*),(?P<ALTP>[^,]*),(?P<CC_BAND>[^,]*),(?P<LOUT>[^,]*),(?P<HLD>[^,]*),(?P<QUICK_KEY>[^,]*),(?P<NUMBER_TAG>[^,]*),(?P<ALT_COLOR>[^,]*),(?P<ALT_PATTERN>[^,]*))?',
		},


		b'CLR': {	# CLR
			'recmd': rb'CLR,(?P<ANS>[^,]*)',
		},


		b'CNT': {	# CNT
			'recmd': rb'CNT,(?P<CONTRAST>[^,]*)',
		},


		b'COM': {	# COM
			'recmd': rb'COM,(?P<BAUDRATE>[^,]*)(:?,(?P<RSV1>[^,]*))?',
		},


		b'CSC': {	# CSC
			'recmd': rb'CSC,(?P<RSSI>[^,]*)(:?,(?P<FRQ>[^,]*),(?P<SQL>[^,]*))?',
		},


		b'CSG': {	# CSG
			'recmd': rb'CSG,(?P<ANS>[^,]*)',
		},


		b'CSP': {	# CSP
			'recmd': rb'CSP,(?P<NAME>[^,]*)(:?,(?P<LIMIT_L>[^,]*),(?P<LIMIT_H>[^,]*),(?P<STP>[^,]*),(?P<MOD>[^,]*),(?P<ATT>[^,]*),(?P<DLY>[^,]*),(?P<RSV1>[^,]*),(?P<HLD>[^,]*),(?P<LOUT>[^,]*),(?P<C-CH>[^,]*),(?P<RSV2>[^,]*),(?P<RSV3>[^,]*),(?P<QUICK_KEY>[^,]*),(?P<START_KEY>[^,]*),(?P<RSV4>[^,]*),(?P<NUMBER_TAG>[^,]*),(?P<AGC_ANALOG>[^,]*),(?P<AGC_DIGITAL>[^,]*),(?P<P25WAITING>[^,]*))?',
		},


		b'CSY': {	# CSY
			'recmd': rb'CSY,(?P<SYS_INDEX>[^,]*)',
		},


		b'DBC': {	# DBC
			'recmd': rb'DBC,(?P<STEP>[^,]*)(:?,(?P<MOD>[^,]*))?',
		},


		b'DCH': {	# DCH
			'recmd': rb'DCH,(?P<ANS>[^,]*)',
		},


		b'DGR': {	# DGR
			'recmd': rb'DGR,(?P<ANS>[^,]*)',
		},


		b'DLA': {	# DLA
			'recmd': rb'DLA,(?P<ANS>[^,]*)',
		},


		b'DSY': {	# DSY
			'recmd': rb'DSY,(?P<ANS>[^,]*)',
		},


		b'EPG': {	# EPG
			'recmd': rb'EPG,(?P<ANS>[^,]*)',
		},


		b'FWD': {	# FWD
			'recmd': rb'FWD,(?P<INDEX>[^,]*)',
		},


		b'GDO': {	# GDO
			'recmd': rb'GDO,(?P<DISP_MODE>[^,]*)(:?,(?P<UNIT>[^,]*),(?P<TIME_FORMAT>[^,]*),(?P<TIME_ZONE>[^,]*),(?P<POS_FORMAT>[^,]*))?',
		},


		b'GID': {	# GID
			'recmd': rb'GID,(?P<SITE_TYPE>[^,]*),(?P<TGID>[^,]*),(?P<ID_SRCH_MODE>[^,]*),(?P<NAME1>[^,]*),(?P<NAME2>[^,]*),(?P<NAME3>[^,]*)',
		},


		b'GIE': {	# GIE
			'recmd': rb'GIE,(?P<FRQ>[^,]*)',
		},


		b'GIN': {	# GIN
			'recmd': rb'GIN,(?P<GRP_TYPE>[^,]*)(:?,(?P<NAME>[^,]*),(?P<QUICK_KEY>[^,]*),(?P<LOUT>[^,]*),(?P<REV_INDEX>[^,]*),(?P<FWD_INDEX>[^,]*),(?P<SYS_INDEX>[^,]*),(?P<CHN_HEAD>[^,]*),(?P<CHN_TAIL>[^,]*),(?P<SEQ_NO>[^,]*),(?P<LATITUDE>[^,]*),(?P<LONGITUDE>[^,]*),(?P<RANGE>[^,]*),(?P<GPSENABLE>[^,]*))?',
		},


		b'GLF': {	# GLF
			'recmd': rb'GLF,(?P<FRQ>[^,]*)',
		},


		b'GLG': {	# GLG
			'recmd': rb'GLG,(?P<FRQ_TGID>[^,]*),(?P<MOD>[^,]*),(?P<ATT>[^,]*),(?P<CTCSS_DCS>[^,]*),(?P<NAME1>[^,]*),(?P<NAME2>[^,]*),(?P<NAME3>[^,]*),(?P<SQL>[^,]*),(?P<MUT>[^,]*),(?P<SYS_TAG>[^,]*),(?P<CHAN_TAG>[^,]*),(?P<P25NAC>[^,]*)',
		},


		b'GLI': {	# GLI
			'recmd': rb'GLI,(?P<TGID>[^,]*)',
		},


		b'JNT': {	# JNT
			'recmd': rb'JNT,(?P<ANS>[^,]*)',
		},


		b'JPM': {	# JPM
			'recmd': rb'JPM,(?P<ANS>[^,]*)',
		},


		b'KBP': {	# KBP
			'recmd': rb'KBP,(?P<LEVEL>[^,]*)(:?,(?P<LOCK>[^,]*),(?P<SAFE>[^,]*))?',
		},


		b'KEY': {	# KEY
			'recmd': rb'KEY,(?P<ANS>[^,]*)',
		},


		b'LIH': {	# LIH
			'recmd': rb'LIH,(?P<INDEX>[^,]*)',
		},


		b'LIN': {	# LIN
			'recmd': rb'LIN,(?P<LAS_TYPE>[^,]*)(:?,(?P<NAME>[^,]*),(?P<LOUT>[^,]*),(?P<ALT>[^,]*),(?P<ALTL>[^,]*),(?P<REV_INDEX>[^,]*),(?P<FWD_INDEX>[^,]*),(?P<SEQ_NO>[^,]*),(?P<LATITUDE>[^,]*),(?P<LONGITUDE>[^,]*),(?P<RANGE>[^,]*),(?P<SPEED>[^,]*),(?P<DIR>[^,]*),(?P<ALT_COLOR>[^,]*),(?P<ALT_PATTERN>[^,]*))?',
		},


		b'LIT': {	# LIT
			'recmd': rb'LIT,(?P<INDEX>[^,]*)',
		},


		b'LOF': {	# LOF
			'recmd': rb'LOF,(?P<ANS>[^,]*)',
		},


		b'LOI': {	# LOI
			'recmd': rb'LOI,(?P<SYS_INDEX>[^,]*)(:?,(?P<TGID>[^,]*))?',
		},


		b'MCP': {	# MCP
			'recmd': rb'MCP,(?P<LOWER1>[^,]*)(:?,(?P<UPPER1>[^,]*),(?P<STEP1>[^,]*),(?P<OFFSET1>[^,]*),(?P<LOWER2>[^,]*),(?P<UPPER2>[^,]*),(?P<STEP2>[^,]*),(?P<OFFSET2>[^,]*),(?P<LOWER3>[^,]*),(?P<UPPER3>[^,]*),(?P<STEP3>[^,]*),(?P<OFFSET3>[^,]*),(?P<LOWER4>[^,]*),(?P<UPPER4>[^,]*),(?P<STEP4>[^,]*),(?P<OFFSET4>[^,]*),(?P<LOWER5>[^,]*),(?P<UPPER5>[^,]*),(?P<STEP5>[^,]*),(?P<OFFSET5>[^,]*),(?P<LOWER6>[^,]*),(?P<UPPER6>[^,]*),(?P<STEP6>[^,]*),(?P<OFFSET6>[^,]*))?',
		},


		b'MDL': {	# MDL
			'recmd': rb'MDL,(?P<MODEL>[^,]*)',
		},


		b'MEM': {	# MEM
			'recmd': rb'MEM,(?P<MEMORY_USED>[^,]*),(?P<SYS>[^,]*),(?P<SITE>[^,]*),(?P<CHN>[^,]*),(?P<LOC>[^,]*)',
		},


		b'MNU': {	# MNU
			'recmd': rb'MNU,(?P<ANS>[^,]*)',
		},


		b'OMS': {	# OMS
			'recmd': rb'OMS,(?P<L1_CHAR>[^,]*)(:?,(?P<L2_CHAR>[^,]*),(?P<L3_CHAR>[^,]*),(?P<L4_CHAR>[^,]*))?',
		},


		b'P25': {	# P25
			'recmd': rb'P25,(?P<RSV1>[^,]*),(?P<RSV2>[^,]*),(?P<ERR_RATE>[^,]*)',
		},


		b'POF': {	# POF
			'recmd': rb'POF,(?P<ANS>[^,]*)',
		},


		b'PRG': {	# PRG
			'recmd': rb'PRG,(?P<ANS>[^,]*)',
		},


		b'PRI': {	# PRI
			'recmd': rb'PRI,(?P<PRI_MODE>[^,]*)(:?,(?P<MAX_CHAN>[^,]*),(?P<INTERVAL>[^,]*))?',
		},


		b'PWR': {	# PWR
			'recmd': rb'PWR,(?P<RSSI>[^,]*),(?P<FRQ>[^,]*)',
		},


		b'QGL': {	# QGL
			'recmd': rb'QGL,(?P<STATUS>[^,]*)',
		},


		b'QSC': {	# QSC
			'recmd': rb'QSC,(?P<RSSI>[^,]*)(:?,(?P<FRQ>[^,]*),(?P<SQL>[^,]*))?',
		},


		b'QSH': {	# QSH
			'recmd': rb'QSH,(?P<ANS>[^,]*)',
		},


		b'QSL': {	# QSL
			'recmd': rb'QSL,(?P<PAGE0>[^,]*)(:?,(?P<PAGE1>[^,]*),(?P<PAGE2>[^,]*),(?P<PAGE3>[^,]*),(?P<PAGE4>[^,]*),(?P<PAGE5>[^,]*),(?P<PAGE6>[^,]*),(?P<PAGE7>[^,]*),(?P<PAGE8>[^,]*),(?P<PAGE9>[^,]*))?',
		},


		b'REV': {	# REV
			'recmd': rb'REV,(?P<INDEX>[^,]*)',
		},


		b'RIE': {	# RIE
			'recmd': rb'RIE,(?P<ANS>[^,]*)',
		},


		b'RMB': {	# RMB
			'recmd': rb'RMB,(?P<FREE>[^,]*)',
		},


		b'SCN': {	# SCN
			'recmd': rb'SCN,(?P<DISP_MODE>[^,]*)(:?,(?P<RSV1>[^,]*),(?P<CH_LOG>[^,]*),(?P<G_ATT>[^,]*),(?P<RSV2>[^,]*),(?P<P25_LPF>[^,]*),(?P<RSV3>[^,]*),(?P<RSV4>[^,]*),(?P<RSV5>[^,]*),(?P<RSV6>[^,]*),(?P<RSV7>[^,]*),(?P<RSV8>[^,]*),(?P<RSV9>[^,]*),(?P<RSV10>[^,]*),(?P<RSV11>[^,]*),(?P<RSV12>[^,]*),(?P<RSV13>[^,]*),(?P<RSV14>[^,]*),(?P<RSV15>[^,]*),(?P<RSV16>[^,]*),(?P<RSV17>[^,]*))?',
		},


		b'SCO': {	# SCO
			'recmd': rb'SCO,(?P<ANS>[^,]*),(?P<MOD>[^,]*),(?P<ATT>[^,]*),(?P<DLY>[^,]*),(?P<RSV1>[^,]*),(?P<CODE_SRCH>[^,]*),(?P<BSC>[^,]*),(?P<REP>[^,]*),(?P<RSV2>[^,]*),(?P<RSV3>[^,]*),(?P<MAX_STORE>[^,]*),(?P<RSV4>[^,]*),(?P<AGC_ANALOG>[^,]*),(?P<AGC_DIGITAL>[^,]*),(?P<P25WAITING>[^,]*)',
		},


		b'SCT': {	# SCT
			'recmd': rb'SCT,(?P<COUNT>[^,]*)',
		},


		b'SGP': {	# SGP
			'recmd': rb'SGP,(?P<NAME>[^,]*)(:?,(?P<FIPS1>[^,]*),(?P<FIPS2>[^,]*),(?P<FIPS3>[^,]*),(?P<FIPS4>[^,]*),(?P<FIPS5>[^,]*),(?P<FIPS6>[^,]*),(?P<FIPS7>[^,]*),(?P<FIPS8>[^,]*))?',
		},


		b'SHK': {	# SHK
			'recmd': rb'SHK,(?P<SRCH_KEY_1>[^,]*)(:?,(?P<SRCH_KEY_2>[^,]*),(?P<SRCH_KEY_3>[^,]*),(?P<RSV1>[^,]*),(?P<RSV2>[^,]*),(?P<RSV3>[^,]*))?',
		},


		b'SIF': {	# SIF
			'recmd': rb'SIF,(?P<RSV1>[^,]*),(?P<NAME>[^,]*),(?P<QUICK_KEY>[^,]*),(?P<HLD>[^,]*),(?P<LOUT>[^,]*),(?P<MOD>[^,]*),(?P<ATT>[^,]*),(?P<C_CH>[^,]*),(?P<RSV2>[^,]*),(?P<RSV3>[^,]*),(?P<REV_INDEX>[^,]*),(?P<FWD_INDEX>[^,]*),(?P<SYS_INDEX>[^,]*),(?P<CHN_HEAD>[^,]*),(?P<CHN_TAIL>[^,]*),(?P<SEQ_NO>[^,]*),(?P<START_KEY>[^,]*),(?P<LATITUDE>[^,]*),(?P<LONGITUDE>[^,]*),(?P<RANGE>[^,]*),(?P<GPS_ENABLE>[^,]*),(?P<RSV4>[^,]*),(?P<MOT_TYPE>[^,]*),(?P<EDACS_TYPE>[^,]*),(?P<P25WAITING>[^,]*),(?P<RSV5>[^,]*)',
		},


		b'SIH': {	# SIH
			'recmd': rb'SIH,(?P<SYS_INDEX>[^,]*)',
		},


		b'SIN': {	# SIN
			'recmd': rb'SIN,(?P<SYS_TYPE>[^,]*)(:?,(?P<NAME>[^,]*),(?P<QUICK_KEY>[^,]*),(?P<HLD>[^,]*),(?P<LOUT>[^,]*),(?P<DLY>[^,]*),(?P<RSV1>[^,]*),(?P<RSV2>[^,]*),(?P<RSV3>[^,]*),(?P<RSV4>[^,]*),(?P<RSV5>[^,]*),(?P<REV_INDEX>[^,]*),(?P<FWD_INDEX>[^,]*),(?P<CHN_GRP_HEAD>[^,]*),(?P<CHN_GRP_TAIL>[^,]*),(?P<SEQ_NO>[^,]*),(?P<START_KEY>[^,]*),(?P<RSV6>[^,]*),(?P<RSV7>[^,]*),(?P<RSV8>[^,]*),(?P<RSV9>[^,]*),(?P<RSV10>[^,]*),(?P<NUMBER_TAG>[^,]*),(?P<AGC_ANALOG>[^,]*),(?P<AGC_DIGITAL>[^,]*),(?P<P25WAITING>[^,]*),(?P<PROTECT>[^,]*),(?P<RSV11>[^,]*))?',
		},


		b'SIT': {	# SIT
			'recmd': rb'SIT,(?P<SYS_INDEX>[^,]*)',
		},


		b'SLI': {	# SLI
			'recmd': rb'SLI,(?P<TGID>[^,]*)',
		},


		b'SQL': {	# SQL
			'recmd': rb'SQL,(?P<LEVEL>[^,]*)',
		},


		b'SSP': {	# SSP
			'recmd': rb'SSP,(?P<SRCH_INDEX>[^,]*)(:?,(?P<DLY>[^,]*),(?P<ATT>[^,]*),(?P<HLD>[^,]*),(?P<LOUT>[^,]*),(?P<QUICK_KEY>[^,]*),(?P<START_KEY>[^,]*),(?P<RSV1>[^,]*),(?P<NUMBER_TAG>[^,]*),(?P<AGC_ANALOG>[^,]*),(?P<AGC_DIGITAL>[^,]*),(?P<P25WAITING>[^,]*))?',
		},


		b'TFQ': {	# TFQ
			'recmd': rb'TFQ,(?P<FRQ>[^,]*)(:?,(?P<LCN>[^,]*),(?P<LOUT>[^,]*),(?P<REV_INDEX>[^,]*),(?P<FWD_INDEX>[^,]*),(?P<SYS_INDEX>[^,]*),(?P<GRP_INDEX>[^,]*),(?P<RSV1>[^,]*),(?P<NUMBER_TAG>[^,]*),(?P<VOL_OFFSET>[^,]*),(?P<RSV2>[^,]*))?',
		},


		b'TIN': {	# TIN
			'recmd': rb'TIN,(?P<NAME>[^,]*)(:?,(?P<TGID>[^,]*),(?P<LOUT>[^,]*),(?P<PRI>[^,]*),(?P<ALT>[^,]*),(?P<ALTL>[^,]*),(?P<REV_INDEX>[^,]*),(?P<FWD_INDEX>[^,]*),(?P<SYS_INDEX>[^,]*),(?P<GRP_INDEX>[^,]*),(?P<RSV1>[^,]*),(?P<AUDIO_TYPE>[^,]*),(?P<NUMBER_TAG>[^,]*),(?P<ALT_COLOR>[^,]*),(?P<ALT_PATTERN>[^,]*),(?P<VOL_OFFSET>[^,]*))?',
		},


		b'TON': {	# TON
			'recmd': rb'TON,(?P<INDEX>[^,]*)(:?,(?P<NAME>[^,]*),(?P<FRQ>[^,]*),(?P<MOD>[^,]*),(?P<ATT>[^,]*),(?P<DLY>[^,]*),(?P<ALT>[^,]*),(?P<ALTL>[^,]*),(?P<TONE_A>[^,]*),(?P<RSV1>[^,]*),(?P<TONE_B>[^,]*),(?P<RSV2>[^,]*),(?P<RSV3>[^,]*),(?P<RSV4>[^,]*),(?P<ALT_COLOR>[^,]*),(?P<ALT_PATTERN>[^,]*),(?P<AGC_ANALOG>[^,]*),(?P<RSV5>[^,]*),(?P<RSV6>[^,]*))?',
		},


		b'TRN': {	# TRN
			'recmd': rb'TRN,(?P<ID_SEARCH>[^,]*)(:?,(?P<S_BIT>[^,]*),(?P<END_CODE>[^,]*),(?P<AFS>[^,]*),(?P<RSV1>[^,]*),(?P<RSV2>[^,]*),(?P<EMG>[^,]*),(?P<EMGL>[^,]*),(?P<FMAP>[^,]*),(?P<CTM_FMAP>[^,]*),(?P<RSV3>[^,]*),(?P<RSV4>[^,]*),(?P<RSV5>[^,]*),(?P<RSV6>[^,]*),(?P<RSV7>[^,]*),(?P<RSV8>[^,]*),(?P<RSV9>[^,]*),(?P<RSV10>[^,]*),(?P<RSV11>[^,]*),(?P<RSV12>[^,]*),(?P<TGID_GRP_HEAD>[^,]*),(?P<TGID_GRP_TAIL>[^,]*),(?P<ID_LOUT_GRP_HEAD>[^,]*),(?P<ID_LOUT_GRP_TAIL>[^,]*),(?P<MOT_ID>[^,]*),(?P<EMG_COLOR>[^,]*),(?P<EMG_PATTERN>[^,]*),(?P<P25NAC>[^,]*),(?P<PRI_ID_SCAN>[^,]*))?',
		},


		b'ULF': {	# ULF
			'recmd': rb'ULF,(?P<FRQ>[^,]*)',
		},


		b'ULI': {	# ULI
			'recmd': rb'ULI,(?P<ANS>[^,]*)',
		},


		b'VER': {	# VER
			'recmd': rb'VER,(?P<VERSION>[^,]*)',
		},


		b'VOL': {	# VOL
			'recmd': rb'VOL,(?P<LEVEL>[^,]*)',
		},


		b'WIN': {	# WIN
			'recmd': rb'WIN,(?P<ANS>[^,]*)',
		},


		b'WXS': {	# WXS
			'recmd': rb'WXS,(?P<DLY>[^,]*)(:?,(?P<ATT>[^,]*),(?P<ALT_PRI>[^,]*),(?P<RSV1>[^,]*),(?P<AGC_ANALOG>[^,]*),(?P<RSV2>[^,]*))?',
		},

	}

	def domatch(tomatch):

		global prematchre, ERRORRESP
	
		def doIt(target, request, basedict, addgroups):
			#print('doIt matching:', target)
			#print('           to:', request)
			regex = re.compile(request, flags = 0)
			rematch = regex.match(target)
			
			if rematch is not None:
				basedict.update(rematch.groupdict(default=b''))
				if addgroups:
					basedict.update({'groups': rematch.groups(default=b'')})
			else:
				 basedict.update({'iserror': True, 'errorcode': Decode.ERR_NOMATCH})
	
		def runIt(target, request, basedict, addgroups = False):
			nonlocal doIt
		
			if isinstance(request, types.FunctionType):
				doIt(target, request(basedict), basedict, addgroups)
		
			elif isinstance(request, bytes):
				doIt(target, request, basedict, addgroups)
		
			else:
				raise ValueError("Invalid decode type")
	
		dec = Decode()
	
		matchresult = {	# Set some default results
			'CMD': b'', 
			'iserror': False, 
			'errorcode': Decode.NO_ERROR,
			'response': tomatch,
		}

		prematch = prematchre.match(tomatch)
		if prematch is None: 
			matchresult.update({'iserror': True, 'errorcode': Decode.ERR_PREMATCH})
		
		else:	# Prematch OK, try the main event
			# Update the results
			matchresult.update(prematch.groupdict())
	
			resp = prematch.group(1)	# What did we find?
			print('Found:', resp)
	
			if resp in ERRORRESP:		# Error response, can't go further
				matchresult.update({'CMD': resp, 'iserror': True, 'errorcode': Decode.ERR_RESPONSE})
		
			elif resp in dec.Decodes:
				matchresult['CMD'] = resp
				# OK, we know what to do ... I hope
		
				# First, run the prematch if it exists
				if 'repre' in dec.Decodes[resp]:
					runIt(tomatch, dec.Decodes[resp]['repre'], matchresult)
			
				# So far, so good. Now run the main event
				if 'recmd' in dec.Decodes[resp]:	# Should usually be there
					runIt(tomatch, dec.Decodes[resp]['recmd'], matchresult, addgroups = True)
				
				if 'repost' in dec.Decodes[resp]:	# Post processing
					dec.Decodes[resp]['repost'](matchresult)
		
			else:
				matchresult.update({'iserror': True, 'errorcode': Decode.ERR_UNKNOWN_RESPONSE})
		
		return matchresult
		
		

class Scanner(Serial):
	"""
	Scanner class - Handles opening IO to the scanner and command write with response read.
	"""
	
	COOKED = 0
	RAW = 1
	DECODED = 2

	def __init__(self, port = None, baudrate = 0, timeout = 0.2, ):
		'''
		Initialize the underlying serial port and provide the wrapper
		'''
		
		Serial.__init__(self, port = port, baudrate = baudrate, timeout = timeout)
		self._sio = io.TextIOWrapper(io.BufferedRWPair(self, self),
			newline='\r', line_buffering=True, encoding = 'ISO-8859-1')
		return
		
	def discover(self):
		'''
		Discover the Scanner port
		
		Currently only the PL2303 is acceptable. This will expand later in development
		'''
		
		if self.port is None:	# Look for the port
			devs_prefix = ['cu.PL2303',] # Just PL2303 devices for now
			pdevs = [glob('/dev/' + pref + '*') for pref in devs_prefix]
			# Use the first match
			for pdev1 in pdevs:
				if len(pdev1) > 0:
					self.port = pdev1[0]
					break
				
		if self.port is None:	# Still bad ... not good
			return False
		
		self.baudrate = 19200	# Temporary default
		
		self.open()
		
		return self.isOpen()

	def cmd(self, cmd_string, cooked = COOKED):
		'''
		Send a command and return the response
		
		The line ending '\r' is automatically added and removed
		'''
				
		self._sio.write(cmd_string + '\r')
		self._sio.flush()	# Note sure we need this ...
		resp = self._sio.readline().encode('ISO-8859-1')
		if resp.endswith(b'\r'): resp = resp[:-1] # Strip the '\r'
		if cooked == self.COOKED:    resp = self.cookIt(resp)
		elif cooked == self.RAW:     pass	# Nothing to do
		elif cooked == self.DECODED: resp = self.decodeIt(resp)
		else: raise ValueError("Scanner.cmd: cooked value out of range")
		
		return resp
		
	def cookIt(self, resp):
		'''
		Create an ascii string from the bytes input
		Any non-ASCII chars (ord >127) are replaced with '?'
		'''
		if not type(resp) is bytes: 
			raise TypeError('Scanner.CookIt(): I can only cook bytes!')
		
		return bytes([c if c < 127 else ord('?') for c in resp]).decode('ASCII')
		
	def decodeIt(self, resp):
		'''
		Decode a raw response into the corresponding structure
		
		NOTE! NOT YET IMPLEMENTED!
		'''
		
		raise NotImplementedError('Scanner.decodeIt: Not Implemented (stay tuned!)')
		