from __future__ import annotations
# from matplotlib import pyplot
from botData.dataObjects import EventPoint
from botUtils import BotPrinter as BUPrint
from botData.settings import Directories

from datetime import datetime, timezone
from random import randint

class GraphMaker():
	"""# GRAPH MAKER
	Used to create graphs from a list of event points;
	Currently only for ps2 events.
	"""

	def CreateGraphAll(p_eventName:str, p_dataList:list[EventPoint]):
		"""# CREATE GRAPH: ALL
		The main function that returns a filepath to a saved graph of the session.
		"""
		from matplotlib import pyplot
		# BUPrint.Debug(f"Using datapoints: \n{p_dataList}")

		# Create individual Arrays for data:
		dataArray_ActiveParticipants = [data.activeParticipants for data in p_dataList]
		dataArray_kills = [data.kills for data in p_dataList]
		dataArray_deaths = [data.deaths for data in p_dataList]
		dataArray_captured = [data.captured for data in p_dataList]
		dataArray_defended = [data.defended for data in p_dataList]
		dataArray_revives = [data.revives for data in p_dataList]
		dataArray_timeStamps = [data.timestamp for data in p_dataList]

		# vFigure:figure.Figure = pyplot.figure()
		pyplot.rcParams["figure.figsize"] = 20, 10
		pyplot.xlabel("Time")
		pyplot.yscale("linear")
		pyplot.yscale("linear")
		pyplot.title(p_eventName)
		pyplot.margins(tight=True)
		pyplot.locator_params(axis="y", integer=True)

		pyplot.plot(dataArray_timeStamps,dataArray_kills, "*-b", label="Kills")
		pyplot.plot(dataArray_timeStamps,dataArray_deaths, "*-r", label="Deaths")
		pyplot.plot(dataArray_timeStamps,dataArray_revives, "+:g", label="Revives")
		pyplot.plot(dataArray_timeStamps,dataArray_captured, "D-c", label="Captures")
		pyplot.plot(dataArray_timeStamps,dataArray_defended, "d-m", label="Defenses")
		pyplot.plot(dataArray_timeStamps, dataArray_ActiveParticipants, "d-.k", label="Players")

		pyplot.legend(loc="upper right")

		vFilePath = f"{Directories.tempDir}{p_eventName}_StatVisAll.png"

		pyplot.savefig(vFilePath)

		pyplot.close()

		return vFilePath