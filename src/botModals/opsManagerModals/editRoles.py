import discord
from botData.dataObjects import OperationData, OpRoleData
from botUtils import BotPrinter as BUPrint
from botData.utilityData import EmojiLibrary
import botModals.opsManagerModals.baseModal as baseModal
from botData.settings import Messages as botMessages
from botData.settings import SignUps

class EditRoles(baseModal.BaseModal):
	txtPingables = discord.ui.TextInput(
		label="Pingables",
		placeholder="Roles to mention in notifications",
		style=discord.TextStyle.short,
		required=False
	)

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
	def __init__(self, p_opData: OperationData):
		super().__init__(p_opData, p_title="Edit Roles")
		self.reservedUsers = [] # Get users who were moved to reserve as a result of this change.

	async def on_submit(self, pInteraction: discord.Interaction):
		BUPrint.Debug("Edit Roles Modal submitted...")
		self.vOpData.pingables = self.txtPingables.value.split(" ")

		vRoleNames = self.txtRoleName.value.splitlines()
		vRoleEmoji = self.txtEmoji.value.splitlines()
		vRoleMax = self.txtRoleMaxPos.value.splitlines()
		
		# If user made an error, don't proceed- inconstsent lengths!
		if len(vRoleNames) != len(vRoleEmoji) != len(vRoleMax):
			await pInteraction.response.send_message('Inconsistent array lengths in fields!  \nMake sure the number of lines matches in all three fields.\n\nFor empty Emojis, use "-".', ephemeral=True)
			return

		vIndex = 0
		vArraySize = len(vRoleNames)
		madeReserve = 0

		if vArraySize > SignUps.maxRoles:
			await pInteraction.response.send_message(f"Too many roles!\nThe max number of roles an event can have is: {SignUps.maxRoles}.")

		BUPrint.Debug(f"Size of array: {len(vRoleNames)}")
		while vIndex < vArraySize:

			vCurrentRole = OpRoleData(roleName=vRoleNames[vIndex], roleIcon=vRoleEmoji[vIndex], maxPositions=int(vRoleMax[vIndex]))
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
						self.vOpData.roles[vIndex].roleIcon = EmojiLibrary.ParseStringToEmoji(vCurrentRole.roleIcon)
					else:
						self.vOpData.roles[vIndex].roleIcon = vCurrentRole.roleIcon

				# Handle overflow (lowering a max limit to a lower number than there are participants) when max positions is higher than 0.
				if self.vOpData.roles[vIndex].players.__len__() > self.vOpData.roles[vIndex].maxPositions and self.vOpData.roles[vIndex].maxPositions > 0:
					BUPrint.Debug(f"Handling overflow of users in role {self.vOpData.roles[vIndex].roleName}.")

					while self.vOpData.roles[vIndex].players.__len__() > self.vOpData.roles[vIndex].maxPositions:
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
					vCurrentRole.roleIcon = EmojiLibrary.ParseStringToEmoji(vCurrentRole.roleIcon)
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
		vPingables: str = ""
		vRoleNames: str = ""
		vRoleEmojis: str = ""
		vRoleMaxPos: str = ""
		vRoleMembers: str = "DISPLAY PURPOSES ONLY\n"

		for pingable in self.vOpData.pingables:
			vPingables += f"{pingable} "

		roleIndex: OpRoleData
		for roleIndex in self.vOpData.roles:
			vRoleNames += f"{roleIndex.roleName}\n"
			vRoleMembers += f"{roleIndex.players}\n"
			vRoleMaxPos += f"{roleIndex.maxPositions}\n"
			if roleIndex.roleIcon == None:
				vRoleEmojis += '-\n'
			else:
				vRoleEmojis += f"{roleIndex.roleIcon}\n"

	# Set the text inputs to existing values:
		self.txtPingables.default = vPingables.strip()
		self.txtRoleName.default = vRoleNames.strip()
		self.txtEmoji.default = vRoleEmojis.strip()
		self.txtRoleMaxPos.default = vRoleMaxPos.strip()
		self.txtRolePlayers.default = vRoleMembers.strip()