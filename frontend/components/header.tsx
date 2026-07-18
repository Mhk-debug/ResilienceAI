import React from "react";
import { Activity } from "lucide-react";

function Header() {
    return (
        <header className="bg-[hsl(224_58%_18%)] px-6 py-4 md:px-10 md:py-5 flex items-center justify-between shadow-lg">
            <div className="flex flex-col gap-0.5">
                <div className="flex items-center gap-2.5">
                    <Activity className="h-5 w-5 text-primary-foreground opacity-80" />
                    <h1 className="text-lg font-bold tracking-tight text-primary-foreground md:text-xl">
                        Earthquake Risk Assessment AI
                    </h1>
                </div>
                <p className="text-xs font-medium tracking-widest text-primary-foreground/50 pl-7 uppercase">
                    codeTrio &nbsp;·&nbsp; STIMU
                </p>
            </div>

            <div className="flex items-center gap-2 rounded-full border border-primary-foreground/20 bg-primary-foreground/10 px-3 py-1.5">
                <span className="text-xs font-semibold text-primary-foreground/90">
                    AI Model Active
                </span>
            </div>
        </header>
    );
}

export default Header;
