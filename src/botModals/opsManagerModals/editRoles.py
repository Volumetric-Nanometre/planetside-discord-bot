import discord
import botData.operations as OpData
from botUtils import BotPrinter as BUPrint
import botModals.opsManagerModals.baseModal as baseModal
import botUtils

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
	# def __init__(self, *, title: str = "Edit Roles", pOpData: OpData.OperationData):

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
			else:
				# Index is a new role, append!
				self.vOpData.roles.append(vCurrentRole)

			vIndex += 1
		# End of while loop.
		BUPrint.Debug("Roles updated!")
		await pInteraction.response.defer()


	# Prefill fields:
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