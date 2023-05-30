"""# OPERATION EDITOR

Classes and functions soley related to editing operation data via discord.
"""

from botData.dataObjects import OperationData, OperationOptions, OpsStatus

# Modals
from botModals.opsManagerModals.editChannels import EditChannels
from botModals.opsManagerModals.editDates import EditDates
from botModals.opsManagerModals.editInfo import EditInfo
from botModals.opsManagerModals.editRoles import EditRoles

import opsManager

from discord.ui import View, Button, Select
from discord import Interaction, Message, ButtonStyle, SelectOption, Embed, NotFound
from enum import Enum

from botUtils import BotPrinter as BUPrint
import copy


class OpEditor():
	"""# Op Editor
	The object used to edit an operation, including live & defaults.
	It does NOT send messages.  This remains with the OperationManager itself.

	The editor holds the message and is tasked with updating it.

	### PARAMETERS
	`p_interaction` - The discord.Interaction that called the command
	`p_opData` - The operation data object to edit. Can be None for new events.
	"""
	def __init__(self, p_interaction:Interaction, p_message: Message, p_opData:OperationData = None):
		self.interaction:Interaction = p_interaction
		"""The interaction that called the editor."""

		self.origMessage:Message = p_message
		"""The message sent for the editor."""

		self.currentPath:str = ""
		"""The current file path of the operations file being edited. Empty if custom."""
		self.originalData: OperationData = p_opData
		"""The original data passed into the editor.  May be NONE!"""

		self.newOpData = OperationData()
		"""The data that, if the user saves or applies, is used."""

		if self.originalData != None:
			self.newOpData = copy.deepcopy(self.originalData)


	async def UpdateEditor(self):
		"""# Update Editor
		Called to update the editors message with an updated embed and view.
		"""
		await self.origMessage.edit(embed=self.CreateEmbed(), view=self.CreateView())

		
	def CreateView(self) -> View:
		"""# Create View
		Returns a view with appropriate button labels & enablement for the status of the data."""
		newView = View(timeout=None)

		newView.add_item(EditorBtn_Date(self))
		newView.add_item(EditorBtn_Info(self))
		newView.add_item(EditorBtn_Roles(self))
		newView.add_item(EditorBtn_Channels(self))

		newView.add_item(EditorBtn_Actions(self))

		newView.add_item(EditorToggleBtn(self, self.newOpData.options.bAutoStart, "Auto Start", self.newOpData.options.SetAutoStart))
		newView.add_item(EditorToggleBtn(self, self.newOpData.options.bUseCompact, "Compact", self.newOpData.options.SetCompact))
		newView.add_item(EditorToggleBtn(self, self.newOpData.options.bIsPS2Event, "PS2 Event", self.newOpData.options.SetIsPs2))
		if self.newOpData.options.bIsPS2Event:
			newView.add_item(EditorToggleBtn(self, self.newOpData.options.bUseSoberdogsFeedback, "Soberdogs", self.newOpData.options.SetSoberFeedback))
		else:
			self.newOpData.options.bUseSoberdogsFeedback = False
		newView.add_item(EditorToggleBtn(self, self.newOpData.options.bUseReserve, "Reserves", self.newOpData.options.SetReserves))

		newView.add_item(EditorBtn_Help())

		return newView


	def CreateEmbed(self) -> Embed:
		newEmbed = Embed(
			title=f"OPERATION EDITOR | {self.newOpData.name}",
			description="Fields below outline the current configuration of the above event."
		)

		newEmbed.add_field(
			name="Info",
			value=self.newOpData.description if self.newOpData.description != "" else "*Not Set*"
		)

		newEmbed.add_field(
			name="Additional Info",
			value=self.newOpData.customMessage if self.newOpData.customMessage != "" else "*Not Set*"
		)

		newEmbed.add_field(
			name="Options",
			value=f"""[{self.newOpData.options.bUseReserve}] Use Reserve
[{self.newOpData.options.bUseCompact}] Use Compact 
[{self.newOpData.options.bAutoStart}] Autostart 
[{self.newOpData.options.bIsPS2Event}] PS2 Event
[{self.newOpData.options.bUseSoberdogsFeedback}] Sober Feedback
"""
		)


		rolesText = ""
		for role in self.newOpData.roles:
			rolesText += f"{role.GetRoleName()}\n"

		newEmbed.add_field(
			name="Roles",
			value=rolesText
		)

		newEmbed.add_field(
			name="Roles",
			value=f"Pingables: {self.newOpData.GetPingables(self.interaction.guild)}\n Managing User: {self.newOpData.managedBy}"
		)


		return newEmbed


# Button row constants
editRow:int = 0 # Primary edit buttons.
toggleRow: int = 2 # Toggle buttons
actionRow: int = 4 # Action dropdown.

# BUTTONS	| BUTTONS	| BUTTONS	| BUTTONS	| BUTTONS	| BUTTONS	|

class EditorBtn(Button):
	def __init__(self, p_btnStyle:ButtonStyle, p_label:str, p_row:int):
		self.parentEditor: OpEditor
		super().__init__(
			style=p_btnStyle,
			label=p_label,
			row=p_row
		)

class EditorToggleBtn(EditorBtn):
	def __init__(self,p_parentEditor:OpEditor, p_option:bool, p_label:str, p_setter:callable):
		self.toggleOpt = p_option
		self.optLabel = p_label
		self.parentEditor = p_parentEditor
		self.optionSetterFunc:callable = p_setter

		styleToUse = None
		label = ""
		if p_option:
			label = f"Disable {self.optLabel}"
			styleToUse = ButtonStyle.secondary
		else:
			label = f"Enable {self.optLabel}"
			styleToUse = ButtonStyle.primary

		super().__init__(
			p_btnStyle=styleToUse,
			p_label=label,
			p_row=toggleRow
		)


	async def callback(self, p_interaction:Interaction):
		self.toggleOpt = not self.toggleOpt
		self.optionSetterFunc(self.toggleOpt)

		await self.parentEditor.UpdateEditor()
		await p_interaction.response.defer()


class EditorBtn_Date(EditorBtn):
	def __init__(self, p_parentEditor: OpEditor):
		self.parentEditor = p_parentEditor

		super().__init__(
			p_btnStyle=ButtonStyle.gray,
			p_label="Edit Date",
			p_row=editRow
		)

	async def callback(self, p_interaction:Interaction):
		modal = EditDates(p_opData=self.parentEditor.newOpData, p_liveOps=opsManager.OperationManager().vLiveOps, p_updateFunction=self.parentEditor.UpdateEditor)
		await p_interaction.response.send_modal(modal)



class EditorBtn_Info(EditorBtn):
	def __init__(self, p_parentEditor: OpEditor):
		self.parentEditor = p_parentEditor

		super().__init__(
			p_btnStyle=ButtonStyle.gray,
			p_label="Edit Info",
			p_row=editRow
		)

	async def callback(self, p_interaction:Interaction):
		modal = EditInfo(p_OpData=self.parentEditor.newOpData, p_updateFunction=self.parentEditor.UpdateEditor)
		await p_interaction.response.send_modal(modal)



class EditorBtn_Roles(EditorBtn):
	def __init__(self, p_parentEditor: OpEditor):
		self.parentEditor = p_parentEditor

		super().__init__(
			p_btnStyle=ButtonStyle.gray,
			p_label="Edit Roles",
			p_row=editRow
		)

	async def callback(self, p_interaction:Interaction):
		modal = EditRoles(p_OpData=self.parentEditor.newOpData, p_updateFunction=self.parentEditor.UpdateEditor)
		await p_interaction.response.send_modal(modal)


class EditorBtn_Channels(EditorBtn):
	def __init__(self, p_parentEditor: OpEditor):
		self.parentEditor = p_parentEditor

		super().__init__(
			p_btnStyle=ButtonStyle.gray,
			p_label="Edit Channels",
			p_row=editRow
		)

	async def callback(self, p_interaction:Interaction):
		modal = EditChannels(p_OpData=self.parentEditor.newOpData, p_updateFunction=self.parentEditor.UpdateEditor)
		await p_interaction.response.send_modal(modal)


class EditorBtn_Help(Button):
	def __init__(self):
		super().__init__(
			label="Help",
			emoji="❓",
			url="https://github.com/LCWilliams/planetside-discord-bot/wiki/Ops-Editor-2"
		)


# ACTIONBAR	|	ACTIONBAR	|	ACTIONBAR	|	ACTIONBAR	|	ACTIONBAR	|

class ActionBarValues(Enum):
	saveDefault = "SAVE_DEFAULT"
	deleteDefault = "DELETE_DEFAULT"
	newLive = "NEW_LIVE_EVENT"
	saveLive = "SAVE_LIVE_EVENT"
	deleteLive = "DELETE_LIVE_EVENT"
	closeEditor = "CLOSE_ON_FINISH"


class EditorBtn_Actions(Select):
	"""# Editor Button: Actions
	A select menu with actions to perform."""

	def __init__(self, p_parentEditor: OpEditor):
		self.parentEditor = p_parentEditor

		self.actionList = [
			SelectOption(label="Save Default",value=ActionBarValues.saveDefault.value, description="Saves the data to a default, overwriting any existing with same name"),
		    SelectOption(label="Delete Default",value=ActionBarValues.deleteDefault.value ,description="Deletes the default with the current event name if present.")]

		optionNewLive = SelectOption(label="Post New event",value=ActionBarValues.newLive.value, description="Creates a new live event and posts it.")
		optionSaveLive = SelectOption(label="Apply Live Changes",value=ActionBarValues.saveLive.value ,description="Save changes to a live operation.")
		optionDeleteLive = SelectOption(label="Delete Live Event",value=ActionBarValues.deleteLive.value , description="Deletes the live event (inc. signup post).")

		if self.parentEditor.newOpData.messageID == "":
			self.actionList.insert(0, optionNewLive)
		else:
			self.actionList.insert(0, optionDeleteLive)
			self.actionList.insert(0, optionSaveLive)

		self.actionList.append(SelectOption(label="Close Editor", value=ActionBarValues.closeEditor.value, description="Closes the editor."))


		super().__init__(
			placeholder="Actions",
			max_values=3,
			options=self.actionList,
			row=actionRow
		)

	async def callback(self, p_interaction:Interaction):
		"""Callback.
		If non destructive and destructive options are chosen for the same type (live/default), the destructive option is ignored."""
		await p_interaction.response.defer(thinking=True, ephemeral=True)

		responseMsg = "Performed:\n"
		actions = self.values

		bIgnoreDefaultDestructive = bool(ActionBarValues.deleteDefault.value in actions and ActionBarValues.saveDefault.value in actions)
		bIgnoreLiveDestructive = bool(ActionBarValues.deleteLive.value in actions and ActionBarValues.saveLive.value in actions)
		
		opsMan = opsManager.OperationManager()


# Perform Actions:
	# NEW LIVE
		if ActionBarValues.newLive.value in actions:
			succesfulPost = await opsMan.AddNewLiveOp(self.parentEditor.newOpData)
			if succesfulPost:
				responseMsg += "[OK]	Add New Event\n"

	# SAVE/UPDATE LIVE
		if ActionBarValues.saveLive.value in actions:
			# Remove reserve users if any present and use reserve is false:
			if not self.parentEditor.newOpData.options.bUseReserve:
				self.parentEditor.newOpData.reserves.clear()

			# If name, date, or signup channel is modified, recreate event (easier than attempting rename)
			if self.parentEditor.newOpData.name != self.parentEditor.originalData.name or self.parentEditor.newOpData.date != self.parentEditor.originalData.date or self.parentEditor.newOpData.targetChannel != self.parentEditor.originalData.targetChannel:
				await opsMan.RemoveOperation(self.parentEditor.originalData)

				self.parentEditor.newOpData.GenerateFileName()
				await opsMan.AddNewLiveOp(self.parentEditor.newOpData)
				responseMsg += "[OK]	Updated event recreated."
		
			else:
				await opsMan.UpdateMessage(self.parentEditor.newOpData)
				responseMsg += "[OK]	Update Event\n"
	
	# DELETE LIVE
		if ActionBarValues.deleteLive.value in actions:
			if bIgnoreLiveDestructive:
				responseMsg += "[FAIL]	Delete Live | Conflicting options\n"
			else:
				succesfulRemove = await opsMan.RemoveOperation(self.parentEditor.newOpData)
				if succesfulRemove:
					responseMsg += "[OK]	Delete Live Event\n"
				else:
					responseMsg += "[FAIL]	Delete Live Event | Consider manual removal of event data & components\n"
		
	# SAVE DEFAULT
		if ActionBarValues.saveDefault.value in actions:
			newDefault = copy.deepcopy(self.parentEditor.newOpData)
			
			# Ensures status is set back to open for future posts.
			newDefault.status = OpsStatus.open

			# Filename must be empty so it is saved as default.
			newDefault.fileName = ""

			# Clear roles of any existing players.
			for role in newDefault.roles:
				role.players.clear()
			
			newDefault.reserves.clear()

			succesfulSave = opsManager.OperationManager.SaveToFile(newDefault)

			if succesfulSave:
				responseMsg += "[OK]	Save Default\n"
			else:
				responseMsg += "[FAIL]	Save Default\n"

	# DELETE DEFAULT
		if ActionBarValues.deleteDefault.value in actions:
			if bIgnoreDefaultDestructive:
				responseMsg += "[FAIL]	Delete Default | Conflisting options\n"
			else:
				tmpMessageID = self.parentEditor.newOpData.messageID
				self.parentEditor.newOpData.messageID = ""
				succesfulRemove = await opsMan.RemoveOperation(self.parentEditor.newOpData)
				self.parentEditor.newOpData.messageID = tmpMessageID

				if succesfulRemove:
					responseMsg += "[OK]	Remove Default\n"
				else:
					responseMsg += "[FAIL]	Remove Default\n"

	
	# CLOSE EDITOR
		if ActionBarValues.closeEditor.value in actions:
			try:
				await self.parentEditor.interaction.delete_original_response()
			except NotFound:
				BUPrint.Debug(" Interaction Edit failed.  Channel likely removed.")		


			if ActionBarValues.deleteLive.value not in actions:
				BUPrint.Debug("Not deleting current live event, re-open & update.")
				self.parentEditor.newOpData.status = OpsStatus.open
				opsManager.OperationManager.SaveToFile(self.parentEditor.newOpData)
				await opsMan.UpdateMessage(self.parentEditor.newOpData)
	
		try:
			await p_interaction.edit_original_response(content=responseMsg)
		except NotFound:
			BUPrint.Debug(" Interaction Edit failed.  Channel likely removed.")		