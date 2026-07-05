"""SimpleArticle agent that appends tool execution results to final output."""

from typing import List

from hello_agents import SimpleAgent
from hello_agents.core.message import Message


class SimpleArticleAgent(SimpleAgent):
	"""SimpleAgent variant that includes tool results in the final response."""

	def run(self, input_text: str, max_tool_iterations: int = 3, **kwargs) -> str:
		"""
		Run agent with optional tool calling and append tool execution results.

		Args:
			input_text: User input.
			max_tool_iterations: Max rounds for tool-call iterations.
			**kwargs: Extra LLM invoke args.

		Returns:
			Final answer with executed tool results appended when available.
		"""
		messages = []
		enhanced_system_prompt = self._get_enhanced_system_prompt()
		messages.append({"role": "system", "content": enhanced_system_prompt})

		for msg in self._history:
			messages.append({"role": msg.role, "content": msg.content})

		messages.append({"role": "user", "content": input_text})

		if not self.enable_tool_calling:
			response = self.llm.invoke(messages, **kwargs)
			self.add_message(Message(input_text, "user"))
			self.add_message(Message(response, "assistant"))
			return response

		current_iteration = 0
		final_response = ""
		last_tool_results: List[str] = []

		while current_iteration < max_tool_iterations:
			response = self.llm.invoke(messages, **kwargs)
			tool_calls = self._parse_tool_calls(response)

			if tool_calls:
				clean_response = response
				current_round_results: List[str] = []

				for call in tool_calls:
					result = self._execute_tool_call(call["tool_name"], call["parameters"])
					current_round_results.append(result)
					clean_response = clean_response.replace(call["original"], "")

				if current_round_results:
					# Only keep the latest round so the final output contains
					# the last tool-call iteration result.
					last_tool_results = current_round_results

				messages.append({"role": "assistant", "content": clean_response})
				tool_results_text = "\n\n".join(current_round_results)
				messages.append(
					{
						"role": "user",
						"content": (
							"工具执行结果：\n"
							f"{tool_results_text}\n\n"
							"请基于这些结果给出完整的回答。"
						),
					}
				)

				current_iteration += 1
				continue

			final_response = response
			break

		if current_iteration >= max_tool_iterations and not final_response:
			final_response = self.llm.invoke(messages, **kwargs)

		if last_tool_results:
			tool_result_block = "\n\n".join(last_tool_results)
			final_response = (
				f"{final_response}\n\n"
				"===== 工具执行结果 =====\n"
				f"{tool_result_block}"
			)

		self.add_message(Message(input_text, "user"))
		self.add_message(Message(final_response, "assistant"))
		return final_response

