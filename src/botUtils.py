import os
import datetime
import settings

# BotPrinter:
# wraps printing around booleans.
class BotPrinter():

	# Convenience function for cleaner code & operation.
	# Only prints if bShowDebug is true.
	@staticmethod
	def Debug(p_string):
		if(settings.bShowDebug):
			print(f"[{datetime.datetime.now()}] {p_string}")

	# Convenience function to pretty print errors.
	@staticmethod
	def LogError(p_string):
		print(f"[{datetime.datetime.now()}] ERROR: {p_string}")

