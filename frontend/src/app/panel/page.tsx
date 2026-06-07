"use client";
import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import api from "@/lib/api";

// ── Types ─────────────────────────────────────────────────────────────────────
interface UserRow {
    username: string; email: string; role: string;
    is_active: boolean; last_active: string | null;
    created_at: string | null; alarm_count: number;
    ai_quota: number;
}
interface Session { username: string; role: string; last_active: string; }
interface LogRow {
    id: number; username: string; action: string;
    details: string; level: string; created_at: string;
}
interface Stats {
    total_users: number; active_users: number;
    total_alarms: number; online_now: number; errors_today: number;
}

// ── Stat Card ─────────────────────────────────────────────────────────────────
function StatCard({ label, value, icon, color }: { label: string; value: number; icon: string; color: string }) {
    return (
        <div className={`glass-panel p-5 rounded-xl border ${color} flex items-center gap-4`}>
            <div className="text-3xl">{icon}</div>
            <div>
                <p className="text-2xl font-black text-white">{value}</p>
                <p className="text-xs text-[var(--color-b-muted)] mt-0.5">{label}</p>
            </div>
        </div>
    );
}

// ── Level Badge ───────────────────────────────────────────────────────────────
const LEVEL_STYLES: Record<string, string> = {
    INFO:    "bg-blue-900/50 text-blue-300 border-blue-700",
    WARNING: "bg-yellow-900/50 text-yellow-300 border-yellow-700",
    ERROR:   "bg-red-900/50 text-red-300 border-red-700",
    DEBUG:   "bg-gray-800 text-gray-400 border-gray-600",
};
function LevelBadge({ level }: { level: string }) {
    return (
        <span className={`px-2 py-0.5 rounded text-xs font-bold border ${LEVEL_STYLES[level] || LEVEL_STYLES.DEBUG}`}>
            {level}
        </span>
    );
}

// ── Main Page ─────────────────────────────────────────────────────────────────
export default function AdminPage() {
    const router = useRouter();
    const [tab, setTab] = useState<"users" | "sessions" | "logs">("users");
    const [stats, setStats] = useState<Stats | null>(null);
    const [users, setUsers] = useState<UserRow[]>([]);
    const [sessions, setSessions] = useState<Session[]>([]);
    const [logs, setLogs] = useState<LogRow[]>([]);
    const [logTotal, setLogTotal] = useState(0);
    const [logPage, setLogPage] = useState(1);
    const [logLevel, setLogLevel] = useState("");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");
    const [updating, setUpdating] = useState<string | null>(null);
    const [showAddUser, setShowAddUser] = useState(false);
    const [newUsername, setNewUsername] = useState("");
    const [newPassword, setNewPassword] = useState("");
    const [newEmail, setNewEmail] = useState("");
    const [newRole, setNewRole] = useState("user");
    const [currentUser, setCurrentUser] = useState("");

    // ── Access guard ───────────────────────────────────────────────────────────────────
    useEffect(() => {
        // Cookie-based auth: /auth/me API üzerinden gerçek rol doğrulaması
        api.get('/auth/me')
            .then(res => {
                const role = res.data?.role;
                const u = res.data?.username;
                setCurrentUser(u || "");
                if (role !== "admin") {
                    router.push("/");
                }
            })
            .catch(() => {
                router.push("/login");
            });
    }, [router]);

    // ── Data fetching ─────────────────────────────────────────────────────────
    const fetchStats = useCallback(async () => {
        try { setStats((await api.get("/admin/stats")).data); }
        catch { /* sessizce geç */ }
    }, []);

    const fetchUsers = useCallback(async () => {
        setLoading(true); setError("");
        try { setUsers((await api.get("/admin/users")).data.users); }
        catch (e: any) { setError(e?.response?.data?.detail || "Kullanıcılar yüklenemedi."); }
        finally { setLoading(false); }
    }, []);

    const fetchSessions = useCallback(async () => {
        setLoading(true); setError("");
        try { setSessions((await api.get("/admin/active-sessions")).data.active_sessions); }
        catch (e: any) { setError(e?.response?.data?.detail || "Oturumlar yüklenemedi."); }
        finally { setLoading(false); }
    }, []);

    const fetchLogs = useCallback(async () => {
        setLoading(true); setError("");
        try {
            const params = new URLSearchParams({ page: String(logPage), per_page: "50" });
            if (logLevel) params.set("level", logLevel);
            const res = await api.get(`/admin/logs?${params}`);
            setLogs(res.data.logs);
            setLogTotal(res.data.total);
        }
        catch (e: any) { setError(e?.response?.data?.detail || "Loglar yüklenemedi."); }
        finally { setLoading(false); }
    }, [logPage, logLevel]);

    useEffect(() => { fetchStats(); }, [fetchStats]);
    useEffect(() => {
        if (tab === "users") fetchUsers();
        else if (tab === "sessions") fetchSessions();
        else if (tab === "logs") fetchLogs();
    }, [tab, fetchUsers, fetchSessions, fetchLogs]);

    // ── User actions ──────────────────────────────────────────────────────────
    const toggleActive = async (username: string, current: boolean) => {
        setUpdating(username);
        try {
            await api.put(`/admin/users/${username}/status`, { is_active: !current });
            setUsers(prev => prev.map(u => u.username === username ? { ...u, is_active: !current } : u));
        } catch (e: any) {
            alert(e?.response?.data?.detail || "Güncelleme başarısız.");
        } finally { setUpdating(null); }
    };

    const changeRole = async (username: string, newRole: string) => {
        setUpdating(username);
        try {
            await api.put(`/admin/users/${username}/status`, { role: newRole });
            setUsers(prev => prev.map(u => u.username === username ? { ...u, role: newRole } : u));
        } catch (e: any) {
            alert(e?.response?.data?.detail || "Rol değiştirilemedi.");
        } finally { setUpdating(null); }
    };

    const changeQuota = async (username: string, newQuota: number) => {
        // Backend zaten admin rolü kontrolu yapıyor; UI'dan admin1 hardcode kaldırıldı
        try {
            setUpdating(username);
            await api.put(`/admin/users/${username}/status`, { ai_quota: newQuota });
            await fetchUsers();
        } catch (e: any) {
            alert(e?.response?.data?.detail || "Kullanıcı kotası güncellenemedi.");
        } finally {
            setUpdating(null);
        }
    };

    const handleAddUser = async (e: React.FormEvent) => {
        e.preventDefault();
        setUpdating("new");
        try {
            await api.post("/auth/register", { username: newUsername, password: newPassword, email: newEmail });
            if (newRole === "admin") {
                await api.put(`/admin/users/${newUsername}/status`, { role: "admin" });
            }
            setShowAddUser(false);
            setNewUsername("");
            setNewPassword("");
            setNewEmail("");
            setNewRole("user");
            fetchUsers();
            fetchStats();
        } catch (e: any) {
            alert(e?.response?.data?.detail || "Kullanıcı eklenemedi.");
        } finally {
            setUpdating(null);
        }
    };

    // ── Render ────────────────────────────────────────────────────────────────
    return (
        <div className="flex w-full h-full flex-col bg-[var(--color-b-bg)] text-[var(--color-b-text)] overflow-y-auto p-6">
            {/* Header */}
            <div className="mb-6">
                <div className="flex items-center gap-3 mb-1">
                    <div className="w-10 h-10 rounded-lg bg-purple-600 flex items-center justify-center text-xl">⚙️</div>
                    <h1 className="text-3xl font-black text-white">Admin Paneli</h1>
                    <span className="px-2 py-0.5 bg-purple-900/60 border border-purple-700 text-purple-300 rounded text-xs font-bold ml-2">ADMIN</span>
                </div>
                <p className="text-[var(--color-b-muted)] text-sm">Sistem yönetimi, kullanıcı kontrolü ve log takibi</p>
            </div>

            {/* Stats */}
            {stats && (
                <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mb-6">
                    <StatCard label="Toplam Kullanıcı"  value={stats.total_users}  icon="👥" color="border-blue-900" />
                    <StatCard label="Aktif Hesap"       value={stats.active_users} icon="✅" color="border-green-900" />
                    <StatCard label="Aktif Alarmlar"    value={stats.total_alarms} icon="🔔" color="border-yellow-900" />
                    <StatCard label="Şu An Online"      value={stats.online_now}   icon="🟢" color="border-emerald-900" />
                    <StatCard label="Bugün Hata"        value={stats.errors_today} icon="🚨" color="border-red-900" />
                </div>
            )}

            {/* Tabs */}
            <div className="flex gap-2 mb-4 border-b border-[var(--color-b-border)]">
                {(["users", "sessions", "logs"] as const).map((t) => {
                    const labels = { users: "👥 Kullanıcı Yönetimi", sessions: "🟢 Canlı Takip", logs: "📋 Sistem Logları" };
                    return (
                        <button
                            key={t}
                            onClick={() => setTab(t)}
                            className={`px-5 py-2.5 text-sm font-semibold rounded-t transition-colors -mb-px border-b-2 ${
                                tab === t
                                    ? "border-purple-500 text-purple-300"
                                    : "border-transparent text-[var(--color-b-muted)] hover:text-white"
                            }`}
                        >
                            {labels[t]}
                        </button>
                    );
                })}
            </div>

            {error && (
                <div className="bg-red-500/10 border border-red-500/30 rounded-lg px-4 py-3 text-red-400 text-sm mb-4">
                    ⚠️ {error}
                </div>
            )}

            {/* ── TAB: Kullanıcı Yönetimi ── */}
            {tab === "users" && (
                <div className="flex flex-col gap-4 flex-1">
                    {/* Her admin kullanıcı ekleyebilir (backend zaten rolü kontrol ediyor) */}
                    <div className="flex justify-end">
                        <button
                            onClick={() => setShowAddUser(!showAddUser)}
                            className="bg-[var(--color-b-yellow)] text-[#181a20] px-4 py-2 rounded-lg font-bold text-sm hover:bg-[#f0c929] transition-colors"
                        >
                            {showAddUser ? "✕ İptal" : "+ Yeni Kullanıcı Ekle"}
                        </button>
                    </div>

                    {showAddUser && (
                        <form onSubmit={handleAddUser} className="glass-panel p-5 rounded-xl border border-[var(--color-b-border)] grid grid-cols-1 md:grid-cols-5 gap-3 items-end">
                            <div>
                                <label className="block text-xs text-[var(--color-b-muted)] mb-1">Kullanıcı Adı</label>
                                <input required value={newUsername} onChange={e => setNewUsername(e.target.value)} className="w-full bg-[#1e2329] border border-[var(--color-b-border)] rounded px-3 py-2 text-sm text-white" />
                            </div>
                            <div>
                                <label className="block text-xs text-[var(--color-b-muted)] mb-1">Şifre</label>
                                <input required type="password" value={newPassword} onChange={e => setNewPassword(e.target.value)} className="w-full bg-[#1e2329] border border-[var(--color-b-border)] rounded px-3 py-2 text-sm text-white" />
                            </div>
                            <div>
                                <label className="block text-xs text-[var(--color-b-muted)] mb-1">E-posta (Opsiyonel)</label>
                                <input value={newEmail} onChange={e => setNewEmail(e.target.value)} className="w-full bg-[#1e2329] border border-[var(--color-b-border)] rounded px-3 py-2 text-sm text-white" />
                            </div>
                            <div>
                                <label className="block text-xs text-[var(--color-b-muted)] mb-1">Rol</label>
                                <select value={newRole} onChange={e => setNewRole(e.target.value)} className="w-full bg-[#1e2329] border border-[var(--color-b-border)] rounded px-3 py-2 text-sm text-white">
                                    <option value="user">User</option>
                                    <option value="admin">Admin</option>
                                </select>
                            </div>
                            <button disabled={updating === "new"} type="submit" className="bg-purple-600 hover:bg-purple-500 text-white font-bold py-2 rounded px-4 text-sm transition-colors disabled:opacity-50">
                                {updating === "new" ? "Ekleniyor..." : "Ekle"}
                            </button>
                        </form>
                    )}

                <div className="glass-panel rounded-xl overflow-hidden flex-1">
                    <table className="w-full text-left border-collapse text-sm">
                        <thead className="bg-[#1e2329] text-[var(--color-b-muted)] sticky top-0">
                            <tr>
                                {["Kullanıcı", "E-posta", "Rol", "Alarmlar", "AI Kota", "Son Aktif", "Durum", "İşlemler"].map(h => (
                                    <th key={h} className="p-4 border-b border-[var(--color-b-border)] font-semibold">{h}</th>
                                ))}
                            </tr>
                        </thead>
                        <tbody>
                            {loading ? (
                                <tr><td colSpan={7} className="p-12 text-center text-[var(--color-b-muted)]">⏳ Yükleniyor...</td></tr>
                            ) : users.length === 0 ? (
                                <tr><td colSpan={7} className="p-12 text-center text-[var(--color-b-muted)]">Kullanıcı bulunamadı.</td></tr>
                            ) : users.map(u => (
                                <tr key={u.username} className="hover:bg-[#1e2329] transition-colors border-b border-[var(--color-b-border)]">
                                    <td className="p-4 font-bold text-white">{u.username}</td>
                                    <td className="p-4 text-[var(--color-b-muted)]">{u.email || "—"}</td>
                                    <td className="p-4">
                                        <span className={`px-2 py-0.5 rounded text-xs font-bold border ${
                                            u.role === "admin"
                                                ? "bg-purple-900/50 text-purple-300 border-purple-700"
                                                : "bg-gray-800 text-gray-400 border-gray-600"
                                        }`}>
                                            {u.role}
                                        </span>
                                    </td>
                                    <td className="p-4 text-[var(--color-b-yellow)] font-bold">{u.alarm_count}</td>
                                    <td className="p-4">
                                        <div className="flex items-center gap-2">
                                            <span className="text-[var(--color-b-yellow)] font-bold">{u.ai_quota ?? 0}</span>
                                            {/* Tüm adminler kota düzenleyebilir */}
                                            <div className="flex flex-col gap-0.5">
                                                <button onClick={() => {
                                                    const val = prompt(`${u.username} için yeni kota:`, String(u.ai_quota ?? 0));
                                                    if (val !== null && !isNaN(parseInt(val, 10))) {
                                                        changeQuota(u.username, parseInt(val, 10));
                                                    }
                                                }} disabled={updating === u.username} className="text-[10px] bg-purple-900/50 hover:bg-purple-600 px-2 rounded disabled:opacity-50 text-white leading-none py-1 border border-purple-700">
                                                    ✏️ Düzenle
                                                </button>
                                            </div>
                                        </div>
                                    </td>
                                    <td className="p-4 text-[var(--color-b-muted)] text-xs">
                                        {u.last_active ? new Date(u.last_active).toLocaleString("tr-TR") : "—"}
                                    </td>
                                    <td className="p-4">
                                        <span className={`px-2 py-0.5 rounded text-xs font-bold ${
                                            u.is_active
                                                ? "bg-green-900/50 text-green-400 border border-green-800"
                                                : "bg-red-900/50 text-red-400 border border-red-800"
                                        }`}>
                                            {u.is_active ? "Aktif" : "Askıda"}
                                        </span>
                                    </td>
                                    <td className="p-4">
                                        {u.username !== currentUser ? (
                                            <div className="flex gap-2 flex-wrap">
                                                <button
                                                    onClick={() => toggleActive(u.username, u.is_active)}
                                                    disabled={updating === u.username}
                                                    className={`text-xs px-3 py-1.5 rounded border transition-colors disabled:opacity-50 ${
                                                        u.is_active
                                                            ? "border-red-700 text-red-400 hover:bg-red-900/30"
                                                            : "border-green-700 text-green-400 hover:bg-green-900/30"
                                                    }`}
                                                >
                                                    {u.is_active ? "Askıya Al" : "Aktif Et"}
                                                </button>
                                                <button
                                                    onClick={() => changeRole(u.username, u.role === "admin" ? "user" : "admin")}
                                                    disabled={updating === u.username}
                                                    className="text-xs px-3 py-1.5 rounded border border-purple-700 text-purple-400 hover:bg-purple-900/30 transition-colors disabled:opacity-50"
                                                >
                                                    {u.role === "admin" ? "User Yap" : "Admin Yap"}
                                                </button>
                                            </div>
                                        ) : (
                                            <span className="text-[var(--color-b-muted)] text-xs italic">Kendi hesabınız</span>
                                        )}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
                </div>
            )}

            {/* ── TAB: Canlı Takip ── */}
            {tab === "sessions" && (
                <div className="space-y-3">
                    <div className="flex items-center justify-between mb-2">
                        <p className="text-sm text-[var(--color-b-muted)]">Son 15 dakika içinde aktif olan kullanıcılar</p>
                        <button onClick={fetchSessions} className="text-xs px-3 py-1.5 rounded border border-[var(--color-b-border)] text-[var(--color-b-muted)] hover:text-white hover:border-white/30 transition-colors">
                            🔄 Yenile
                        </button>
                    </div>
                    {loading ? (
                        <div className="glass-panel p-12 rounded-xl text-center text-[var(--color-b-muted)]">⏳ Yükleniyor...</div>
                    ) : sessions.length === 0 ? (
                        <div className="glass-panel p-16 rounded-xl text-center">
                            <div className="text-5xl mb-3">😴</div>
                            <p className="text-white font-semibold">Şu an aktif kullanıcı yok</p>
                            <p className="text-[var(--color-b-muted)] text-sm mt-1">Son 15 dakikada işlem yapan kimse bulunmuyor.</p>
                        </div>
                    ) : sessions.map((s, i) => (
                        <div key={i} className="glass-panel p-4 rounded-xl border border-[var(--color-b-border)] flex items-center justify-between">
                            <div className="flex items-center gap-3">
                                <div className="w-2.5 h-2.5 rounded-full bg-green-400 animate-pulse"></div>
                                <div>
                                    <p className="font-bold text-white">{s.username}</p>
                                    <p className="text-xs text-[var(--color-b-muted)]">
                                        Son aktivite: {new Date(s.last_active).toLocaleString("tr-TR")}
                                    </p>
                                </div>
                            </div>
                            <span className={`px-2 py-0.5 rounded text-xs font-bold border ${
                                s.role === "admin"
                                    ? "bg-purple-900/50 text-purple-300 border-purple-700"
                                    : "bg-gray-800 text-gray-400 border-gray-600"
                            }`}>
                                {s.role}
                            </span>
                        </div>
                    ))}
                </div>
            )}

            {/* ── TAB: Sistem Logları ── */}
            {tab === "logs" && (
                <div className="flex flex-col flex-1 gap-3">
                    {/* Filtreler */}
                    <div className="flex gap-2 items-center flex-wrap">
                        {(["", "INFO", "WARNING", "ERROR"] as const).map(lvl => (
                            <button
                                key={lvl || "all"}
                                onClick={() => { setLogLevel(lvl); setLogPage(1); }}
                                className={`text-xs px-3 py-1.5 rounded border font-bold transition-colors ${
                                    logLevel === lvl
                                        ? "border-[var(--color-b-yellow)] text-[var(--color-b-yellow)] bg-yellow-900/20"
                                        : "border-[var(--color-b-border)] text-[var(--color-b-muted)] hover:text-white"
                                }`}
                            >
                                {lvl || "Tümü"}
                            </button>
                        ))}
                        <span className="text-xs text-[var(--color-b-muted)] ml-2">Toplam: {logTotal} kayıt</span>
                    </div>

                    <div className="glass-panel rounded-xl overflow-hidden flex-1 font-mono text-xs">
                        <table className="w-full border-collapse">
                            <thead className="bg-[#1e2329] text-[var(--color-b-muted)] sticky top-0">
                                <tr>
                                    {["Zaman", "Seviye", "Kullanıcı", "İşlem", "Detay"].map(h => (
                                        <th key={h} className="p-3 border-b border-[var(--color-b-border)] text-left font-semibold">{h}</th>
                                    ))}
                                </tr>
                            </thead>
                            <tbody>
                                {loading ? (
                                    <tr><td colSpan={5} className="p-12 text-center text-[var(--color-b-muted)]">⏳ Yükleniyor...</td></tr>
                                ) : logs.length === 0 ? (
                                    <tr><td colSpan={5} className="p-12 text-center text-[var(--color-b-muted)]">Log kaydı bulunamadı.</td></tr>
                                ) : logs.map(log => (
                                    <tr
                                        key={log.id}
                                        className={`border-b border-[var(--color-b-border)] transition-colors ${
                                            log.level === "ERROR" ? "hover:bg-red-950/30" :
                                            log.level === "WARNING" ? "hover:bg-yellow-950/30" :
                                            "hover:bg-[#1e2329]"
                                        }`}
                                    >
                                        <td className="p-3 text-[var(--color-b-muted)] whitespace-nowrap">
                                            {log.created_at ? new Date(log.created_at).toLocaleString("tr-TR") : "—"}
                                        </td>
                                        <td className="p-3"><LevelBadge level={log.level} /></td>
                                        <td className="p-3 text-white font-bold">{log.username}</td>
                                        <td className="p-3 text-[var(--color-b-yellow)]">{log.action}</td>
                                        <td className="p-3 text-[var(--color-b-muted)] max-w-xs truncate">{log.details || "—"}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>

                    {/* Pagination */}
                    {logTotal > 50 && (
                        <div className="flex justify-center gap-2 pt-2">
                            <button
                                onClick={() => setLogPage(p => Math.max(1, p - 1))}
                                disabled={logPage === 1}
                                className="px-4 py-2 rounded border border-[var(--color-b-border)] text-sm text-[var(--color-b-muted)] hover:text-white disabled:opacity-40 transition-colors"
                            >
                                ← Önceki
                            </button>
                            <span className="px-4 py-2 text-sm text-[var(--color-b-muted)]">
                                Sayfa {logPage} / {Math.ceil(logTotal / 50)}
                            </span>
                            <button
                                onClick={() => setLogPage(p => p + 1)}
                                disabled={logPage * 50 >= logTotal}
                                className="px-4 py-2 rounded border border-[var(--color-b-border)] text-sm text-[var(--color-b-muted)] hover:text-white disabled:opacity-40 transition-colors"
                            >
                                Sonraki →
                            </button>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}
