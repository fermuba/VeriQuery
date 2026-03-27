import React, { useEffect, useRef, useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "./useAuth";
import { Shield, ArrowRight, Lock, CheckCircle } from "lucide-react";
import logo from "../assets/logo.png";

export const Login = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { isAuthenticated, isLoading, login, error } = useAuth();
  const redirectTimeoutRef = useRef(null);
  const [checkingAuth, setCheckingAuth] = useState(true);
  const [isLoginLoading, setIsLoginLoading] = useState(false);

  useEffect(() => {
    if (location.pathname === "/callback") {
      const params = new URLSearchParams(location.search);
      const hashParams = new URLSearchParams(location.hash.substring(1));
      
      const hasCode = params.has("code") || hashParams.has("code");
      const hasError = params.has("error") || hashParams.has("error");
      
      if (hasError) {
        const errorMsg = params.get("error") || hashParams.get("error");
        console.error("❌ Error:", errorMsg);
        setCheckingAuth(false);
        return;
      }
      
      if (!hasCode && !isLoading) {
        setCheckingAuth(false);
        return;
      }
      
      if (!isLoading) {
        if (isAuthenticated) {
          redirectTimeoutRef.current = setTimeout(() => {
            navigate("/dashboard", { replace: true });
          }, 300);
        } else {
          setCheckingAuth(false);
        }
      }
      return;
    }

    if (location.pathname === "/login" && isAuthenticated && !isLoading) {
      redirectTimeoutRef.current = setTimeout(() => {
        navigate("/dashboard", { replace: true });
      }, 100);
      return;
    }

    if (!isLoading) {
      setCheckingAuth(false);
    }
  }, [isAuthenticated, isLoading, navigate, location.pathname, checkingAuth]);

  const handleLogin = async () => {
    try {
      setIsLoginLoading(true);
      if (location.pathname === "/callback") {
        navigate("/login", { replace: true });
        setIsLoginLoading(false);
        return;
      }
      await login();
    } catch (err) {
      console.error("❌ Login failed:", err);
      setIsLoginLoading(false);
    }
  };

  if (checkingAuth || (location.pathname === "/callback" && isLoading)) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-slate-50 flex items-center justify-center px-4">
        <div className="space-y-8 text-center">
          <div className="flex justify-center">
            <div className="relative">
              <div className="absolute inset-0 bg-slate-700/10 blur-lg rounded-full"></div>
              <img src={logo} alt="VeriQuery Logo" className="w-20 h-20 object-contain relative transition-transform hover:scale-105 duration-300" />
            </div>
          </div>
          <div>
            <div className="text-slate-700 text-sm font-medium">
              Completando autenticación segura...
            </div>
            <div className="mt-4 flex justify-center gap-2">
              <div className="w-2 h-2 bg-slate-700 rounded-full animate-bounce" style={{animationDelay: '0s'}}></div>
              <div className="w-2 h-2 bg-slate-700 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
              <div className="w-2 h-2 bg-slate-700 rounded-full animate-bounce" style={{animationDelay: '0.4s'}}></div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-slate-50 flex items-center justify-center px-4 relative overflow-hidden">
      {/* Subtle background accents */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-0 right-0 w-96 h-96 bg-slate-100/30 rounded-full blur-3xl"></div>
        <div className="absolute bottom-0 left-0 w-96 h-96 bg-slate-100/20 rounded-full blur-3xl"></div>
      </div>

      {/* Content */}
      <div className="relative z-10 w-full max-w-md pt-10">
        {/* Logo */}
        <div className="text-center mb-12">
          <div className="flex justify-center mb-6">
            <div className="relative">
              <div className="absolute inset-0 bg-slate-700/10 blur-lg rounded-lg"></div>
              <div className="relative bg-slate-900 p-4 rounded-2xl shadow-lg overflow-hidden flex items-center justify-center">
                <img src={logo} alt="VeriQuery" className="w-16 h-16 object-contain" />
              </div>
            </div>
          </div>
          <h1 className="text-4xl font-bold text-gray-900 mb-2" style={{fontFamily: 'Plus Jakarta Sans'}}>
            VeriQuery
          </h1>
          <p className="text-gray-500 text-sm tracking-wide uppercase">Forensic Data Analysis</p>
        </div>

        {/* Card */}
        <div className="bg-white border border-gray-200 rounded-2xl p-8 shadow-lg">
          {/* Security Badge */}
          <div className="flex items-center justify-center gap-2 mb-8 px-4 py-2 rounded-full bg-green-50 border border-green-200 w-fit mx-auto">
            <div className="w-2 h-2 bg-green-600 rounded-full animate-pulse"></div>
            <span className="text-xs font-medium text-green-700">Conexión segura verificada</span>
          </div>

          {/* Title */}
          <div className="text-center mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Acceso Seguro</h2>
            <p className="text-gray-600 text-sm">
              Autenticación empresarial con Microsoft Entra ID
            </p>
          </div>

          {/* Error */}
          {error && (
            <div className="mb-6 p-4 rounded-lg bg-red-50 border border-red-200">
              <p className="text-sm text-red-700">{error}</p>
            </div>
          )}

          {/* Login Button */}
          <button
            onClick={handleLogin}
            disabled={isLoginLoading}
            className="w-full bg-slate-800 hover:bg-slate-900 disabled:bg-gray-400 text-white font-semibold py-3 px-6 rounded-lg flex items-center justify-center gap-2 transition-all duration-200 shadow-md hover:shadow-lg"
          >
            {isLoginLoading ? (
              <>
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                <span>Conectando...</span>
              </>
            ) : (
              <>
                <Lock className="w-5 h-5" strokeWidth={2} />
                <span>Iniciar sesión con Microsoft</span>
                <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" strokeWidth={2} />
              </>
            )}
          </button>

          {/* Security Info */}
          <div className="mt-8 pt-6 border-t border-gray-200 space-y-3">
            <div className="flex items-start gap-3 text-sm">
              <Shield className="w-4 h-4 text-slate-700 mt-0.5 flex-shrink-0" strokeWidth={2} />
              <span className="text-gray-700">Protegido por autenticación multinivel</span>
            </div>
            <div className="flex items-start gap-3 text-sm">
              <Lock className="w-4 h-4 text-slate-700 mt-0.5 flex-shrink-0" strokeWidth={2} />
              <span className="text-gray-700">Cumplimiento con estándares empresariales</span>
            </div>
            <div className="flex items-start gap-3 text-sm">
              <CheckCircle className="w-4 h-4 text-green-600 mt-0.5 flex-shrink-0" strokeWidth={2} />
              <span className="text-gray-700">Sesión encriptada end-to-end</span>
            </div>
          </div>
        </div>

        {/* Footer */}
        <p className="text-center text-gray-500 text-xs mt-8">
          © 2026 VeriQuery. Todos los derechos reservados.
        </p>
      </div>
    </div>
  );
};

export default Login;
