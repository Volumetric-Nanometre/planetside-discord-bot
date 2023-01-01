import discord
import botData.operations as OpData
from botUtils import BotPrinter as BUPrint
import botModals.opsManagerModals.baseModal as baseModal
import botUtils
from botData.settings import Messages as botMessages

class EditRoles(baseModal.BaseModal):
	txtEmoji = discord.ui.TextInput(
		label="Emoji",
		placeholder="EmojiID String per line",
		style=discord.TextStyle.paragraph,
		required=True
	)
	txtRoleName = discord.ui.TextInput(
		label="Role Name",
		placeholder="Light Assault\nHeavy Assault\nEtc...",
		style=discord.TextStyle.paragraph,
		required=True
	)
	txtRoleMaxPos = discord.ui.TextInput(
		label="Max Positions",
		placeholder="Max positions.",
		style=discord.TextStyle.paragraph,
		required=True
	)
	txtRolePlayers = discord.ui.TextInput(
		label="Players",
		placeholder="Player IDs",
		style=discord.TextStyle.paragraph,
		required=False
	)
	def __init__(self, p_opData: OpData.OperationData):
		super().__init__(p_opData, p_title="Edit Roles")
		self.reservedUsers = [] # Get users who were moved to reserve as a result of this change.

	async def on_submit(self, pInteraction: discord.Interaction):
		BUPrint.Debug("Edit Roles Modal submitted...")
		vRoleNames = self.txtRoleName.value.splitlines()
		vRoleEmoji = self.txtEmoji.value.splitlines()
		vRoleMax = self.txtRoleMaxPos.value.splitlines()
		
		# If user made an error, don't proceed- inconstsent lengths!
		if len(vRoleNames) != len(vRoleEmoji) != len(vRoleMax):
			await pInteraction.response.send_message('Inconsistent array lengths in fields!  \nMake sure the number of lines matches in all three fields.\n\nFor empty Emojis, use "".', ephemeral=True)
			return

		vIndex = 0
		vArraySize = len(vRoleNames)
		madeReserve = 0

		botUtils.BotPrinter.Debug(f"Size of array: {len(vRoleNames)}")
		while vIndex < vArraySize:

			vCurrentRole = OpData.OpRoleData(roleName=vRoleNames[vIndex], roleIcon=vRoleEmoji[vIndex], maxPositions=int(vRoleMax[vIndex]))
			if vIndex < len(self.vOpData.roles) :
				# Index is on an existing role, adjust values to keep any signed up users.
				self.vOpData.roles[vIndex].roleName = vCurrentRole.roleName
				self.vOpData.roles[vIndex].maxPositions = vCurrentRole.maxPositions
				if vCurrentRole.roleIcon == "-" or vCurrentRole.roleIcon == '""' or vCurrentRole.roleIcon == "":
					BUPrint.Debug("Setting role icon to NONE")
					self.vOpData.roles[vIndex].roleIcon = "-"
				else:
					# If using a shorthand, parse:
					if vCurrentRole.roleIcon.startswith("ICON_"):
						BUPrint.Debug("Icon library icon specified, parsing for result...")
						self.vOpData.roles[vIndex].roleIcon = botUtils.EmojiLibrary.ParseStringToEmoji(vCurrentRole.roleIcon)
					else:
						self.vOpData.roles[vIndex].roleIcon = vCurrentRole.roleIcon

				# Handle overflow (lowering a max limit to a lower number than there are participants).
				if len(self.vOpData.roles[vIndex].players) > self.vOpData.roles[vIndex].maxPositions:
					while (len(self.vOpData.roles[vIndex].players) > self.vOpData.roles[vIndex].maxPositions):
						madeReserve += 1
						lastUserID = self.vOpData.roles[vIndex].players.pop()
						affectedUser = pInteraction.guild.get_member(lastUserID)
						self.reservedUsers.append(affectedUser.mention)
						if self.vOpData.options.bUseReserve:
							self.vOpData.reserves.insert(0, lastUserID)
			else:
				# Index is a new role, append!
				if vCurrentRole.roleIcon.startswith("ICON_"):
					BUPrint.Debug("Icon library icon specified, parsing for result...")
					botUtils.EmojiLibrary.ParseStringToEmoji(vCurrentRole.roleIcon)
				self.vOpData.roles.append(vCurrentRole)

			vIndex += 1
		# End of while loop.

		BUPrint.Debug("Roles updated!")
		if madeReserve != 0 and self.vOpData.options.bUseReserve:
			await pInteraction.response.send_message(f"ATTENTION: {madeReserve} user(s) will be moved to reserve as a result of this edit if you Apply:\n{self.reservedUsers}", ephemeral=True)

		elif madeReserve != 0 and not self.vOpData.options.bUseReserve:
			await pInteraction.response.send_message(f"ATTENTION: {madeReserve} user(s) will be removed from this event as a result of this edit if you Apply:\n{self.reservedUsers}", ephemeral=True)

		else:
			await pInteraction.response.defer()



	def PresetFields(self):
		BUPrint.Debug("Auto-filling modal (ROLES) with existing data.")
		
		vRoleNames: str = ""
		vRoleEmojis: str = ""
		vRoleMembers: str = "DISPLAY PURPOSES ONLY\n"
		vRoleMaxPos: str = ""

		roleIndex: OpData.OpRoleData
		for roleIndex in self.vOpData.roles:
			vRoleNames += f"{roleIndex.roleName}\n"
			vRoleMembers += f"{roleIndex.players}\n"
			vRoleMaxPos += f"{roleIndex.maxPositions}\n"
			if roleIndex.roleIcon == None:
				vRoleEmojis += '-\n'
			else:
				vRoleEmojis += f"{roleIndex.roleIcon}\n"

	# Set the text inputs to existing values:
		self.txtRoleName.default = vRoleNames.strip()
		self.txtEmoji.default = vRoleEmojis.strip()
		self.txtRoleMaxPos.default = vRoleMaxPos.strip()
		self.txtRolePlayers.default = vRoleMembers.strip()