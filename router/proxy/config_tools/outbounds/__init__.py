import importlib
import pkgutil

from ....target import logger
from ..data_types.outbound import Outbound

registry: dict[str, type[Outbound]] = {}


# 遍历包下的所有模块
for _, module_name, _ in pkgutil.iter_modules(__path__):
    # 动态导入每个模块
    full_mdl_name = f"{__name__}.{module_name}"
    module = importlib.import_module(full_mdl_name)

    # 遍历模块内的所有属性
    for attr_name in dir(module):
        symbol = getattr(module, attr_name)
        # 判断是否是类，且继承了 Outbound
        if (
            not isinstance(symbol, type)
            or not issubclass(symbol, Outbound)
            or symbol is Outbound
        ):
            continue

        name = getattr(symbol, "TYPE", None)
        if name is None:
            raise TypeError(
                f"包 {full_mdl_name} 中的 {attr_name} 继承了 Outbound，但没有实现 TYPE 静态属性"
            )

        logger.dim(f"注册 {name} 类")
        registry[name] = symbol


def parse_url(url: str) -> Outbound | None:
    for name, cls in registry.items():
        if cls.can_parse(url):
            try:
                outbound = cls(url)
            except Exception:
                logger.error(f"处理 {name} 连接失败: {url}")
                raise
            return outbound
