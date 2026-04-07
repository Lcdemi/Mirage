package main

import (
	webview "github.com/webview/webview_go"
)

func popupHTML() string {
	return `<!DOCTYPE html>
<html lang="en">
<head>
	<meta charset="UTF-8">
	<meta name="viewport" content="width=device-width, initial-scale=1.0">
	<title>Puzzled</title>
	<style>
		:root {
			--bg-1: #0f172a;
			--bg-2: #1e293b;
			--card: rgba(15, 23, 42, 0.82);
			--card-edge: rgba(255, 255, 255, 0.22);
			--title: #fef3c7;
			--body: #e2e8f0;
			--accent: #f97316;
			--accent-2: #22d3ee;
		}

		* {
			box-sizing: border-box;
		}

		body {
			margin: 0;
			min-height: 100vh;
			display: grid;
			place-items: center;
			overflow: hidden;
			font-family: "Trebuchet MS", "Lucida Sans Unicode", sans-serif;
			background:
				radial-gradient(circle at 15% 20%, rgba(249, 115, 22, 0.26), transparent 34%),
				radial-gradient(circle at 85% 80%, rgba(34, 211, 238, 0.24), transparent 32%),
				linear-gradient(145deg, var(--bg-1), var(--bg-2));
			color: var(--body);
		}

		.glow {
			position: absolute;
			width: 48vmax;
			height: 48vmax;
			border-radius: 50%;
			filter: blur(48px);
			opacity: 0.2;
			animation: drift 10s ease-in-out infinite alternate;
			z-index: 0;
		}

		.glow.left {
			top: -20vmax;
			left: -14vmax;
			background: var(--accent);
		}

		.glow.right {
			right: -16vmax;
			bottom: -18vmax;
			background: var(--accent-2);
			animation-delay: 1.2s;
		}

		.panel {
			position: relative;
			z-index: 1;
			width: min(90vw, 560px);
			padding: 28px;
			border: 1px solid var(--card-edge);
			border-radius: 22px;
			background: var(--card);
			backdrop-filter: blur(8px);
			box-shadow: 0 18px 55px rgba(2, 6, 23, 0.5);
			animation: rise 480ms ease-out;
		}

		h1 {
			margin: 0;
			line-height: 1.08;
			font-size: clamp(30px, 6vw, 44px);
			font-family: "Impact", "Haettenschweiler", "Arial Narrow Bold", sans-serif;
			letter-spacing: 0.02em;
			color: var(--title);
			text-align: center;
			text-shadow: 0 5px 18px rgba(249, 115, 22, 0.32);
		}

		p {
			margin: 14px 0 0;
			font-size: 16px;
			line-height: 1.5;
			color: #cbd5e1;
		}

		.gif-wrap {
			margin-top: 18px;
			border-radius: 14px;
			overflow: hidden;
			border: 1px solid rgba(255, 255, 255, 0.2);
			box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.12), 0 12px 26px rgba(2, 6, 23, 0.48);
		}

		.gif-wrap img {
			display: block;
			width: 100%;
			height: 380px;
			object-fit: cover;
		}

		@keyframes rise {
			from {
				transform: translateY(12px) scale(0.98);
				opacity: 0;
			}
			to {
				transform: translateY(0) scale(1);
				opacity: 1;
			}
		}

		@keyframes drift {
			from {
				transform: translate(-10px, 8px) scale(1);
			}
			to {
				transform: translate(12px, -9px) scale(1.08);
			}
		}
	</style>
</head>
<body>
	<div class="glow left"></div>
	<div class="glow right"></div>

	<main class="panel">
		<h1>You Have Been Puzzled!</h1>

		<div class="gif-wrap">
			<img src="https://c.tenor.com/TsxrgLdEsRoAAAAd/tenor.gif" alt="Puzzled reaction">
		</div>
	</main>
</body>
</html>`
}

func showPopup() {
	w := webview.New(false)
	defer w.Destroy()
	w.SetTitle("Puzzler")
	w.SetSize(620, 590, webview.HintNone)
	w.SetHtml(popupHTML())
	w.Run()
}

func main() {
	showPopup()
}
