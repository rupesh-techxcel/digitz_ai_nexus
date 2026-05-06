(function () {
	function setActivePanel(panel) {
		document.querySelectorAll(".workspace-nav-btn").forEach((btn) => {
			btn.classList.toggle("active", btn.dataset.panel === panel);
		});

		document.querySelectorAll(".workspace-panel").forEach((el) => {
			el.classList.toggle("active", el.id === `panel-${panel}`);
		});
	}

	function bindWorkspaceNav() {
		document.querySelectorAll(".workspace-nav-btn").forEach((btn) => {
			btn.addEventListener("click", () => {
				setActivePanel(btn.dataset.panel);
			});
		});
	}

	window.scrollToSection = function (id) {
		document.getElementById(id)?.scrollIntoView({ behavior: "smooth" });
	};

	window.openNexusChat = function () {
		document.querySelector(".nexus-chat-launcher")?.click();
	};

	window.sendScenarioPrompt = function (text) {
		if (window.nexusSendMessage) {
			window.nexusSendMessage(text);
		} else {
			window.openNexusChat();
			setTimeout(() => {
				window.nexusSendMessage && window.nexusSendMessage(text);
			}, 400);
		}
	};

	document.addEventListener("DOMContentLoaded", function () {
		bindWorkspaceNav();
		setActivePanel("search");
	});
})();