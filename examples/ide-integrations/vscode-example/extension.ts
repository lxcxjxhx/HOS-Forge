/**
 * HOS-Forge VSCode Extension Example
 *
 * Demonstrates how to integrate HOS-Forge security skills
 * (nuclei_scan, semgrep_scan) into a VSCode extension.
 *
 * Prerequisites:
 *   - VSCode ^1.85.0
 *   - HOS-Forge MCP server running at http://localhost:8000
 *   - nuclei CLI installed and in PATH
 *   - semgrep CLI installed and in PATH
 */

import * as vscode from "vscode";
import * as http from "http";

const HOSServerURL = "http://localhost:8000";

// ---------- MCP HTTP helper ----------

function callMCPTool(
  toolName: string,
  args: Record<string, unknown>
): Promise<any> {
  return new Promise((resolve, reject) => {
    const body = JSON.stringify({ arguments: args });
    const url = new URL(
      `/tools/${toolName}/execute`,
      HOSServerURL
    );

    const req = http.request(
      {
        hostname: url.hostname,
        port: url.port,
        path: url.pathname,
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Content-Length": Buffer.byteLength(body),
        },
      },
      (res) => {
        let data = "";
        res.on("data", (chunk: string) => (data += chunk));
        res.on("end", () => {
          try {
            resolve(JSON.parse(data));
          } catch {
            reject(new Error(`Invalid JSON: ${data}`));
          }
        });
      }
    );

    req.on("error", reject);
    req.write(body);
    req.end();
  });
}

// ---------- nuclei_scan ----------

async function runNucleiScan() {
  const target = await vscode.window.showInputBox({
    prompt: "Enter target URL or IP for Nuclei scan",
    placeHolder: "https://example.com",
  });
  if (!target) return;

  const severityItems = [
    "info",
    "low",
    "medium",
    "high",
    "critical",
  ];
  const severity = await vscode.window.showQuickPick(severityItems, {
    placeHolder: "Select minimum severity (or press Escape for all)",
  });

  const outputChannel = vscode.window.createOutputChannel("HOS Nuclei");
  outputChannel.show(true);
  outputChannel.appendLine(`[nuclei_scan] Scanning: ${target}`);
  if (severity) {
    outputChannel.appendLine(`[nuclei_scan] Severity filter: ${severity}`);
  }

  try {
    const result = await callMCPTool("nuclei_scan", {
      target,
      ...(severity ? { severity } : {}),
    });

    const total: number = result.total ?? 0;
    outputChannel.appendLine(`\nScan complete — ${total} finding(s)\n`);

    if (Array.isArray(result.findings)) {
      for (const f of result.findings) {
        const name = f?.info?.name ?? "Unknown";
        const sev = f?.info?.severity ?? "unknown";
        const matched = f?.matchedAt ?? f?.host ?? "";
        outputChannel.appendLine(`  [${sev.toUpperCase()}] ${name}`);
        outputChannel.appendLine(`    at ${matched}`);
      }
    }
  } catch (err: any) {
    outputChannel.appendLine(`Error: ${err.message}`);
    vscode.window.showErrorMessage(`Nuclei scan failed: ${err.message}`);
  }
}

// ---------- semgrep_scan ----------

async function runSemgrepScan() {
  const defaultPath =
    vscode.workspace.workspaceFolders?.[0]?.uri.fsPath ?? ".";

  const scanPath = await vscode.window.showInputBox({
    prompt: "Enter file or directory path for Semgrep scan",
    value: defaultPath,
  });
  if (!scanPath) return;

  const languages = [
    "python",
    "javascript",
    "typescript",
    "java",
    "go",
    "rust",
  ];
  const language = await vscode.window.showQuickPick(languages, {
    placeHolder: "Select language (or press Escape for auto-detect)",
  });

  const outputChannel = vscode.window.createOutputChannel("HOS Semgrep");
  outputChannel.show(true);
  outputChannel.appendLine(`[semgrep_scan] Scanning path: ${scanPath}`);
  if (language) {
    outputChannel.appendLine(`[semgrep_scan] Language: ${language}`);
  }

  try {
    const result = await callMCPTool("semgrep_scan", {
      path: scanPath,
      ...(language ? { language } : {}),
      config: "auto",
    });

    const total: number = result.total ?? 0;
    outputChannel.appendLine(`\nScan complete — ${total} finding(s)\n`);

    if (Array.isArray(result.findings)) {
      for (const f of result.findings) {
        const checkId = f?.check_id ?? "unknown-rule";
        const filePath = f?.path ?? "";
        const line = f?.start?.line ?? 0;
        const msg = f?.extra?.message ?? "";
        const sev = f?.extra?.severity ?? "INFO";
        outputChannel.appendLine(`  [${sev}] ${checkId}`);
        outputChannel.appendLine(`    ${filePath}:${line}`);
        outputChannel.appendLine(`    ${msg}`);
      }
    }
  } catch (err: any) {
    outputChannel.appendLine(`Error: ${err.message}`);
    vscode.window.showErrorMessage(`Semgrep scan failed: ${err.message}`);
  }
}

// ---------- activation ----------

export function activate(context: vscode.ExtensionContext) {
  console.log("HOS-Forge extension activated");

  context.subscriptions.push(
    vscode.commands.registerCommand("hos.scan.nuclei", runNucleiScan),
    vscode.commands.registerCommand("hos.scan.semgrep", runSemgrepScan)
  );
}

export function deactivate() {
  console.log("HOS-Forge extension deactivated");
}
