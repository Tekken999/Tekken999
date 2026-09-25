package com.rangecoach.app;

import android.Manifest;
import android.app.Activity;
import android.content.ActivityNotFoundException;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.net.Uri;
import android.os.Bundle;
import android.speech.tts.TextToSpeech;
import android.view.WindowManager;
import android.webkit.JavascriptInterface;
import android.webkit.PermissionRequest;
import android.webkit.ValueCallback;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceRequest;
import android.webkit.WebResourceResponse;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;

import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.util.HashMap;
import java.util.Map;

/**
 * Hosts the Range Coach web app in a WebView. Files are served from the APK's
 * assets over https://appassets.androidplatform.net so the page is a secure
 * context (required for camera access) and works fully offline.
 */
public class MainActivity extends Activity {
    private static final String HOST = "appassets.androidplatform.net";
    private static final int REQ_CAMERA = 1;
    private static final int REQ_FILE = 2;

    private WebView web;
    private PermissionRequest pendingPermission;
    private ValueCallback<Uri[]> fileCallback;
    private TextToSpeech tts;
    private boolean ttsReady;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        getWindow().setStatusBarColor(0xFF0D2B20);
        getWindow().setNavigationBarColor(0xFF0D2B20);

        web = new WebView(this);
        web.setBackgroundColor(0xFF0D2B20);
        setContentView(web);

        WebSettings s = web.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);
        s.setMediaPlaybackRequiresUserGesture(false);
        s.setAllowFileAccess(false);
        s.setAllowContentAccess(true);

        web.setWebViewClient(new WebViewClient() {
            @Override
            public WebResourceResponse shouldInterceptRequest(WebView view, WebResourceRequest request) {
                return serveAsset(request.getUrl());
            }

            // String variant: still called on API 24+ and available in the API 23 SDK we compile with.
            @Override
            @SuppressWarnings("deprecation")
            public boolean shouldOverrideUrlLoading(WebView view, String link) {
                Uri url = Uri.parse(link);
                if (HOST.equals(url.getHost())) return false;
                // External links open in the browser.
                try {
                    startActivity(new Intent(Intent.ACTION_VIEW, url));
                } catch (ActivityNotFoundException ignored) {
                }
                return true;
            }
        });

        web.setWebChromeClient(new WebChromeClient() {
            @Override
            public void onPermissionRequest(final PermissionRequest request) {
                runOnUiThread(new Runnable() {
                    @Override
                    public void run() {
                        if (checkSelfPermission(Manifest.permission.CAMERA) == PackageManager.PERMISSION_GRANTED) {
                            request.grant(new String[]{PermissionRequest.RESOURCE_VIDEO_CAPTURE});
                        } else {
                            if (pendingPermission != null) pendingPermission.deny();
                            pendingPermission = request;
                            requestPermissions(new String[]{Manifest.permission.CAMERA}, REQ_CAMERA);
                        }
                    }
                });
            }

            @Override
            public boolean onShowFileChooser(WebView view, ValueCallback<Uri[]> callback, FileChooserParams params) {
                if (fileCallback != null) fileCallback.onReceiveValue(null);
                fileCallback = callback;
                try {
                    startActivityForResult(params.createIntent(), REQ_FILE);
                } catch (ActivityNotFoundException e) {
                    fileCallback = null;
                    return false;
                }
                return true;
            }
        });

        tts = new TextToSpeech(this, new TextToSpeech.OnInitListener() {
            @Override
            public void onInit(int status) {
                ttsReady = status == TextToSpeech.SUCCESS;
            }
        });
        web.addJavascriptInterface(new Bridge(), "AndroidApp");

        if (savedInstanceState == null) {
            web.loadUrl("https://" + HOST + "/index.html");
        } else {
            web.restoreState(savedInstanceState);
        }
    }

    /** Exposed to JavaScript as window.AndroidApp. */
    private class Bridge {
        @JavascriptInterface
        public void speak(String text) {
            if (ttsReady) tts.speak(text, TextToSpeech.QUEUE_FLUSH, null, "rc");
        }

        @JavascriptInterface
        public void stopSpeaking() {
            if (ttsReady) tts.stop();
        }
    }

    private WebResourceResponse serveAsset(Uri url) {
        if (!HOST.equals(url.getHost())) return null;
        String path = url.getPath();
        if (path == null || path.equals("/") || path.isEmpty()) path = "/index.html";
        Map<String, String> headers = new HashMap<>();
        headers.put("Cache-Control", "no-cache");
        headers.put("Access-Control-Allow-Origin", "*");
        try {
            InputStream in = getAssets().open("www" + path);
            return new WebResourceResponse(mimeType(path), null, 200, "OK", headers, in);
        } catch (IOException e) {
            return new WebResourceResponse("text/plain", "utf-8", 404, "Not Found", headers,
                    new ByteArrayInputStream(new byte[0]));
        }
    }

    private static String mimeType(String path) {
        if (path.endsWith(".html")) return "text/html";
        if (path.endsWith(".js") || path.endsWith(".mjs")) return "text/javascript";
        if (path.endsWith(".css")) return "text/css";
        if (path.endsWith(".wasm")) return "application/wasm";
        if (path.endsWith(".json")) return "application/json";
        if (path.endsWith(".png")) return "image/png";
        if (path.endsWith(".svg")) return "image/svg+xml";
        return "application/octet-stream";
    }

    @Override
    public void onRequestPermissionsResult(int requestCode, String[] permissions, int[] results) {
        if (requestCode != REQ_CAMERA || pendingPermission == null) return;
        if (results.length > 0 && results[0] == PackageManager.PERMISSION_GRANTED) {
            pendingPermission.grant(new String[]{PermissionRequest.RESOURCE_VIDEO_CAPTURE});
        } else {
            pendingPermission.deny();
        }
        pendingPermission = null;
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        if (requestCode == REQ_FILE && fileCallback != null) {
            fileCallback.onReceiveValue(WebChromeClient.FileChooserParams.parseResult(resultCode, data));
            fileCallback = null;
            return;
        }
        super.onActivityResult(requestCode, resultCode, data);
    }

    @Override
    public void onBackPressed() {
        // Let the web app go back to its home screen first; exit from home.
        web.evaluateJavascript("window.__androidBack ? window.__androidBack() : false", new ValueCallback<String>() {
            @Override
            public void onReceiveValue(String handled) {
                if (!"true".equals(handled)) finish();
            }
        });
    }

    @Override
    protected void onSaveInstanceState(Bundle outState) {
        super.onSaveInstanceState(outState);
        web.saveState(outState);
    }

    @Override
    protected void onDestroy() {
        if (tts != null) tts.shutdown();
        if (web != null) web.destroy();
        super.onDestroy();
    }
}
